package com.nyayasetu.storage;

public record StoredFile(String relativePath, String originalFilename, FileType type, long sizeBytes, String sha256) {}
