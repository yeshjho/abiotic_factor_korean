package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	CompSize              = 0x10000 // default size of a compression block. Haven't seen any others
	PackUtocVersion       = 3
	CompressionNameLength = 32
)

func listFilesInDir(dir string, pathToChunkID *map[string]FIoChunkID) (*[]GameFileMetaData, error) {
	var files []GameFileMetaData
	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		// only add if it's a file
		if info.IsDir() {
			return nil
		}
		mountedPath, err := filepath.Abs(path)
		if err != nil {
			return err
		}
		mountedPath = strings.TrimPrefix(mountedPath, dir)
		mountedPath = strings.ReplaceAll(mountedPath, "\\", "/") // ensure path dividors are as expected and not Windows
		var offlen FIoOffsetAndLength
		offlen.SetLength(uint64(info.Size()))

		chidData, ok := (*pathToChunkID)[mountedPath]
		if !ok {
			return errors.New("a problem occurred while constructing the file. Did you use the correct manifest file?")
		}
		newEntry := GameFileMetaData{
			filepath: mountedPath,
			chunkID:  chidData,
			offlen:   offlen,
		}
		files = append(files, newEntry)
		return nil
	})

	return &files, err
}

// This function does way too much. It does the following;
// 	- reads all files that must be packed
//  - compresses all the files as specified
//  - records all metadata of packing, required for the program.
//  - writes the compressed files to the .ucas file - not yet encrypted!
func packFilesToUcas(files *[]GameFileMetaData, dir string, outFilename string, compression string) error {
	compMethodNumber := uint8(0)
	if strings.ToLower(compression) != "none" {
		compMethodNumber = 1
	}
	compFun := getCompressionFunction(compression)
	if compFun == nil {
		return errors.New("could not find compression method. Please use none, oodle or zlib")
	}

	// create the new file in a new directory
	directory := filepath.Dir(outFilename)
	os.MkdirAll(directory, 0700)
	f, err := os.OpenFile(outFilename+".ucas", os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close() // all file data is written in this function

	for i := 0; i < len(*files); i++ {
		b, err := os.ReadFile(dir + (*files)[i].filepath)
		if err != nil {
			return err
		}
		(*files)[i].offlen.SetLength(uint64(len(b)))
		if i == 0 {
			(*files)[i].offlen.SetOffset(0)
		} else {
			offset := (*files)[i-1].offlen.GetOffset() + (*files)[i-1].offlen.GetLength()
			offset = ((offset + CompSize - 1) / CompSize) * CompSize // align to 0x1000
			(*files)[i].offlen.SetOffset(offset)
		}
		(*files)[i].metadata.ChunkHash = *sha1Hash(&b)
		(*files)[i].metadata.Flags = 1 // not sure what this should be?

		// now perform compression, write per compressed block to ucas file
		for len(b) != 0 {
			var chunk []byte
			var block FIoStoreTocCompressedBlockEntry
			chunkLen := len(b)
			if chunkLen > CompSize {
				chunkLen = CompSize
			}
			chunk = b[:chunkLen]
			cChunkPtr, err := compFun(&chunk)
			if err != nil {
				return err
			}
			compressedChunk := *cChunkPtr

			block.CompressionMethod = compMethodNumber
			currOffset, _ := f.Seek(0, os.SEEK_CUR)
			block.SetOffset(uint64(currOffset))
			block.SetUncompressedSize(uint32(chunkLen))
			block.SetCompressedSize(uint32(len(compressedChunk)))
			// align this compessedChunk to 0x10 with random bytes as padding
			compressedChunk = append(compressedChunk, getRandomBytes((0x10-(len(compressedChunk)%0x10))&(0x10-1))...)
			b = b[chunkLen:]

			(*files)[i].compressionBlocks = append((*files)[i].compressionBlocks, block)

			// write chunk to the new .ucas file
			f.Write(compressedChunk)
		}
	}
	return nil
}

func (w *DirIndexWrapper) ToBytes() *[]byte {
	buf := bytes.NewBuffer([]byte{})

	dirCount := uint32(len(*w.dirs))
	fileCount := uint32(len(*w.files))
	strCount := uint32(len(*w.strSlice))
	// mount point string
	mountPointStr := stringToFString(MountPoint)
	buf.Write(mountPointStr)

	// directory index entries
	buf.Write(*uint32ToBytes(&dirCount))
	for _, directoryEntry := range *w.dirs {
		binary.Write(buf, binary.LittleEndian, *directoryEntry)
	}

	// file index entries
	buf.Write(*uint32ToBytes(&fileCount))
	for _, fileEntry := range *w.files {
		binary.Write(buf, binary.LittleEndian, *fileEntry)
	}

	// string table
	buf.Write(*uint32ToBytes(&strCount))
	for _, str := range *w.strSlice {
		buf.Write(stringToFString(str))
	}
	output := buf.Bytes()
	return &output
}

func deparseDirectoryIndex(files *[]GameFileMetaData) *[]byte {
	var wrapper DirIndexWrapper
	var dirIndexEntries []*FIoDirectoryIndexEntry
	var fileIndexEntries []*FIoFileIndexEntry

	// first, create unique slice of strings
	strmap := make(map[string]bool)
	for _, v := range *files {
		dirfiles := strings.Split(v.filepath, "/")
		if dirfiles[0] == "" {
			dirfiles = dirfiles[1:]
		}
		for _, str := range dirfiles {
			strmap[str] = true
		}
	}
	strSlice := []string{}
	for k, _ := range strmap {
		strSlice = append(strSlice, k)
	}
	// of this, create a map for quick lookup
	strIdx := make(map[string]int)
	for i, v := range strSlice {
		strIdx[v] = i
	}
	root := FIoDirectoryIndexEntry{
		Name:             NoneEntry,
		FirstChildEntry:  NoneEntry,
		NextSiblingEntry: NoneEntry,
		FirstFileEntry:   NoneEntry,
	}
	dirIndexEntries = append(dirIndexEntries, &root)
	wrapper.dirs = &dirIndexEntries
	wrapper.files = &fileIndexEntries
	wrapper.strTable = &strIdx
	wrapper.strSlice = &strSlice

	for i, v := range *files {
		fpathSections := strings.Split(v.filepath, "/")
		if fpathSections[0] == "" {
			fpathSections = fpathSections[1:]
		}
		root.AddFile(fpathSections, uint32(i), &wrapper)
	}

	return wrapper.ToBytes()
}

func constructUtocFile(files *[]GameFileMetaData, compression string, AESKey []byte) (*[]byte, error) {
	var udata UTocData
	newContainerFlags := uint8(IndexedContainerFlag)

	compressionMethods := []string{"None"}
	if strings.ToLower(compression) != "none" {
		compressionMethods = append(compressionMethods, compression)
		newContainerFlags |= uint8(CompressedContainerFlag)
	}

	if len(AESKey) != 0 {
		newContainerFlags |= uint8(EncryptedContainerFlag)
	}
	compressedBlocksCount := uint32(0)
	for _, v := range *files {
		compressedBlocksCount += uint32(len(v.compressionBlocks))
	}

	dirIndexBytes := deparseDirectoryIndex(files)
	// the container uint64 must be unique and new from any other ID from within the file.
	// There is a low probability that there is a collision with any other uint64 that is already in the file.
	// When this happens, the mod won't work without any apparent reason, so this would be the first place to start investigating.
	var magic [16]byte
	for i := 0; i < len(MagicUtoc); i++ {
		magic[i] = MagicUtoc[i]
	}
	// setting the required header fields
	udata.hdr = UTocHeader{
		Magic:                       magic,
		Version:                     3, // like the Grounded files
		HeaderSize:                  uint32(binary.Size(udata.hdr)),
		EntryCount:                  uint32(len(*files)),
		CompressedBlockEntryCount:   compressedBlocksCount,
		CompressedBlockEntrySize:    12,
		CompressionMethodNameCount:  uint32(len(compressionMethods) - 1), // "extra" methods, other than "none"
		CompressionMethodNameLength: CompressionNameLength,
		CompressionBlockSize:        CompSize,
		DirectoryIndexSize:          uint32(len(*dirIndexBytes)), // number of bytes in the dirIndex
		ContainerID:                 FIoContainerID((*files)[len(*files)-1].chunkID.ID),
		ContainerFlags:              EIoContainerFlags(newContainerFlags),
		PartitionSize:               0xffffffffffffffff,
		PartitionCount:              1,
	}

	buf := bytes.NewBuffer([]byte{})
	// write header
	binary.Write(buf, binary.LittleEndian, udata.hdr)

	// write chunk IDs
	for _, v := range *files {
		binary.Write(buf, binary.LittleEndian, v.chunkID)
	}

	// write Offset and lengths
	for _, v := range *files {
		binary.Write(buf, binary.LittleEndian, v.offlen)
	}

	// write compression blocks
	for _, v := range *files {
		for _, b := range v.compressionBlocks {
			binary.Write(buf, binary.LittleEndian, b)
		}
	}

	// write compression methods, but skip "none"
	for _, compMethod := range compressionMethods {
		if strings.ToLower(compMethod) == "none" {
			continue
		}
		capitalized := strings.Title(compMethod)
		bname := make([]byte, 32)
		for i := 0; i < len(capitalized); i++ {
			bname[i] = capitalized[i]
		}
		binary.Write(buf, binary.LittleEndian, bname)
	}

	// write directory index
	binary.Write(buf, binary.LittleEndian, dirIndexBytes)

	// write chunk metas
	for _, v := range *files {
		binary.Write(buf, binary.LittleEndian, v.metadata)
	}
	output := buf.Bytes()

	return &output, nil
}

// returns the GameFileMetaData of the dependencies file
func packToCasToc(dir string, m *Manifest, outFilename string, compression string, aes []byte) (int, error) {
	// map for quick lookup
	pathToChunkID := make(map[string]FIoChunkID)
	for _, v := range (*m).Files {
		pathToChunkID[v.Filepath] = FromHexString(v.ChunkID)
	}
	// first aggregate flat list of all the files that are in the dir
	// the resulting slice must keep its indices structure.
	fdata, err := listFilesInDir(dir, &pathToChunkID)
	if err != nil {
		return 0, err
	}

	// read each file and place them in a newly created .ucas file with the desired compression method
	// get the required data such as compression sizes and hashes;
	err = packFilesToUcas(fdata, dir, outFilename, compression)
	if err != nil {
		return 0, err
	}

	/* manually add the "dependencies" section here */
	// only include the dependencies that are present
	subsetDependencies := make(map[uint64]FileDependency)
	for _, v := range *fdata {
		// all values are ChunkIDs
		subsetDependencies[v.chunkID.ID] = (*m).Deps.ChunkIDToDependencies[v.chunkID.ID]
	}
	(*m).Deps.ChunkIDToDependencies = subsetDependencies

	// find uint64 of depfile
	depHexString := ""
	for _, v := range (*m).Files {
		if v.Filepath == DepFileName {
			depHexString = v.ChunkID
		}
	}
	depFile := *(*m).Deps.Deparse()
	depFileLength := len(depFile)

	appendUcas, err := os.OpenFile(outFilename+".ucas", os.O_WRONLY|os.O_CREATE, os.ModePerm)
	if err != nil {
		return 0, err
	}
	defer appendUcas.Close()
	// jump to the end of this file
	appendUcas.Seek(0, os.SEEK_END)

	depFileData := GameFileMetaData{
		filepath: "",
		chunkID:  FromHexString(depHexString),
		metadata: FIoStoreTocEntryMeta{
			ChunkHash: *sha1Hash(&depFile),
			Flags:     1,
		},
	}
	depFileData.offlen.SetLength(uint64(depFileLength))

	offset := (*fdata)[len(*fdata)-1].offlen.GetOffset() + (*fdata)[len(*fdata)-1].offlen.GetLength()
	offset = ((offset + CompSize - 1) / CompSize) * CompSize // align to 0x1000
	depFileData.offlen.SetOffset(offset)

	rand.Seed(time.Now().UnixNano())
	depFileData.chunkID.ID = rand.Uint64()

	// code repetition incoming... This should actually be placed in a single function... TODO <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
	compMethodNumber := uint8(0)
	if strings.ToLower(compression) != "none" {
		compMethodNumber = 1
	}
	compFun := getCompressionFunction(compression)
	// now perform compression, write per compressed block to ucas file
	for len(depFile) != 0 {
		var chunk []byte
		var block FIoStoreTocCompressedBlockEntry
		chunkLen := len(depFile)
		if chunkLen > CompSize {
			chunkLen = CompSize
		}
		chunk = depFile[:chunkLen]
		cChunkPtr, err := compFun(&chunk)
		if err != nil {
			return 0, err
		}
		compressedChunk := *cChunkPtr

		block.CompressionMethod = compMethodNumber
		currOffset, _ := appendUcas.Seek(0, os.SEEK_CUR)
		block.SetOffset(uint64(currOffset))
		block.SetUncompressedSize(uint32(chunkLen))
		block.SetCompressedSize(uint32(len(compressedChunk)))
		// align this compessedChunk to 0x10 with random bytes as padding
		compressedChunk = append(compressedChunk, getRandomBytes((0x10-(len(compressedChunk)%0x10))&(0x10-1))...)
		depFile = depFile[chunkLen:]

		depFileData.compressionBlocks = append(depFileData.compressionBlocks, block)

		// write chunk to the new .ucas file
		appendUcas.Write(compressedChunk)
	}
	*fdata = append(*fdata, depFileData)
	// Dependencies file has now been added >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

	// .ucas file has been written now; encrypt with aes if desired (why would you?)
	if len(aes) != 0 {
		b, err := os.ReadFile(outFilename + ".ucas")
		if err != nil {
			return 0, err
		}
		encrypted, err := encryptAES(&b, aes)
		if err != nil {
			return 0, err
		}
		err = os.WriteFile(outFilename+".ucas", *encrypted, os.ModePerm)
		if err != nil {
			return 0, err
		}
	}

	// .utoc file must be generated, especially the directory index, which is the hardest part.
	utocBytes, err := constructUtocFile(fdata, compression, aes)
	if err != nil {
		return 0, err
	}
	err = os.WriteFile(outFilename+".utoc", *utocBytes, os.ModePerm)
	return len(*fdata), err
}
