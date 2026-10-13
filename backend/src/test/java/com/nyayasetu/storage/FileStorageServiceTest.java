package com.nyayasetu.storage;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.nyayasetu.TestProps;
import com.nyayasetu.web.ApiException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockMultipartFile;

class FileStorageServiceTest {

    @TempDir Path dir;
    FileStorageService storage;
    final UUID user = UUID.randomUUID();

    @BeforeEach
    void setUp() throws Exception {
        storage = new FileStorageService(TestProps.props(TestProps.SECRET, dir.toString())); // 1 MB limit
        storage.init();
    }

    private static MockMultipartFile file(String name, byte[] bytes) {
        return new MockMultipartFile("file", name, "application/octet-stream", bytes);
    }

    @Test
    void storesPdfUnderRandomNameAndHashesIt() throws Exception {
        byte[] pdf = "%PDF-1.7\nhello".getBytes(StandardCharsets.US_ASCII);
        StoredFile stored = storage.store(user, file("../../etc/passwd.pdf", pdf));
        assertThat(stored.type()).isEqualTo(FileType.PDF);
        assertThat(stored.originalFilename()).isEqualTo("passwd.pdf");
        assertThat(stored.relativePath()).startsWith(user + "/").endsWith(".pdf").doesNotContain("passwd");
        assertThat(Files.readAllBytes(storage.resolve(stored.relativePath()))).isEqualTo(pdf);
        assertThat(stored.sha256()).hasSize(64);
        assertThat(stored.sizeBytes()).isEqualTo(pdf.length);
        storage.delete(stored.relativePath());
        assertThat(Files.exists(storage.resolve(stored.relativePath()))).isFalse();
    }

    @Test
    void identifiesImagesByContentNotExtension() {
        byte[] png = {(byte) 0x89, 'P', 'N', 'G', 0x0D, 0x0A, 0x1A, 0x0A, 0, 0, 0, 0};
        assertThat(storage.store(user, file("scan.pdf", png)).type()).isEqualTo(FileType.PNG);
        byte[] jpg = {(byte) 0xFF, (byte) 0xD8, (byte) 0xFF, (byte) 0xE0, 0, 0};
        assertThat(storage.store(user, file("x.txt", jpg)).type()).isEqualTo(FileType.JPEG);
    }

    @Test
    void rejectsExecutablesTextAndEmpty() {
        assertThatThrownBy(() -> storage.store(user, file("a.pdf", "MZ\u0090 exe".getBytes(StandardCharsets.ISO_8859_1))))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.code()).isEqualTo("UNSUPPORTED_FILE_TYPE"));
        assertThatThrownBy(() -> storage.store(user, file("a.pdf", "<html>".getBytes())))
                .isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> storage.store(user, file("a.pdf", new byte[0])))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.code()).isEqualTo("EMPTY_FILE"));
    }

    @Test
    void rejectsOversizedFile() {
        byte[] big = new byte[1024 * 1024 + 10];
        System.arraycopy("%PDF-".getBytes(), 0, big, 0, 5);
        assertThatThrownBy(() -> storage.store(user, file("big.pdf", big)))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.code()).isEqualTo("FILE_TOO_LARGE"));
    }

    @Test
    void resolveBlocksPathTraversal() {
        assertThatThrownBy(() -> storage.resolve("../outside.pdf")).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void sanitizesFilenames() {
        assertThat(FileStorageService.sanitizeName(null)).isEqualTo("document");
        assertThat(FileStorageService.sanitizeName("..")).isEqualTo("document");
        assertThat(FileStorageService.sanitizeName("C:\\Users\\me\\RTI reply.pdf")).isEqualTo("RTI reply.pdf");
        assertThat(FileStorageService.sanitizeName("माहिती अर्ज.pdf")).isEqualTo("माहिती अर्ज.pdf");
        assertThat(FileStorageService.sanitizeName("a<b>|c?.pdf")).isEqualTo("a_b_c_.pdf");
    }
}
