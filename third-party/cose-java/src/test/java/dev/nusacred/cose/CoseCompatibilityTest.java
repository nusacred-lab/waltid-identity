package dev.nusacred.cose;

import com.upokecenter.cbor.CBORObject;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.cose.java.*;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.ValueSource;

import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.security.Security;

import static org.junit.jupiter.api.Assertions.*;

class CoseCompatibilityTest {
    private static final byte[] CONTENT = "synthetic competency proof".getBytes(StandardCharsets.UTF_8);
    private static final SecureRandom RANDOM = new SecureRandom();

    @BeforeAll static void installProvider() { Security.addProvider(new BouncyCastleProvider()); }
    @AfterAll static void removeProvider() { Security.removeProvider("BC"); }

    private static byte[] random(int size) {
        byte[] bytes = new byte[size]; RANDOM.nextBytes(bytes); return bytes;
    }

    @ParameterizedTest
    @EnumSource(value = AlgorithmID.class, names = {
        "ECDSA_256", "ECDSA_384", "ECDSA_512", "EDDSA",
        "RSA_PSS_256", "RSA_PSS_384", "RSA_PSS_512"
    })
    void signVerifyRejectTamperingAndWrongHolder(AlgorithmID algorithm) throws Exception {
        OneKey signer = OneKey.generateKey(algorithm);
        OneKey other = OneKey.generateKey(algorithm);
        Sign1Message message = new Sign1Message();
        message.addAttribute(HeaderKeys.Algorithm, algorithm.AsCBOR(), Attribute.PROTECTED);
        message.SetContent(CONTENT);
        message.sign(signer);
        Sign1Message received = (Sign1Message) Message.DecodeFromBytes(message.EncodeToBytes(), MessageTag.Sign1);
        assertTrue(received.validate(signer.PublicKey()));
        assertArrayEquals(CONTENT, received.GetContent());
        assertFalse(received.validate(other.PublicKey()));
        received.SetContent("tampered content");
        assertFalse(received.validate(signer.PublicKey()));
    }

    @Test void externalAuthenticatedDataIsBoundToSignature() throws Exception {
        OneKey signer = OneKey.generateKey(AlgorithmID.ECDSA_256);
        Sign1Message message = new Sign1Message();
        message.addAttribute(HeaderKeys.Algorithm, AlgorithmID.ECDSA_256.AsCBOR(), Attribute.PROTECTED);
        message.SetContent(CONTENT);
        message.setExternal("expected audience".getBytes(StandardCharsets.UTF_8));
        message.sign(signer);
        Sign1Message received = (Sign1Message) Message.DecodeFromBytes(message.EncodeToBytes(), MessageTag.Sign1);
        received.setExternal("expected audience".getBytes(StandardCharsets.UTF_8));
        assertTrue(received.validate(signer.PublicKey()));
        received.setExternal("wrong audience".getBytes(StandardCharsets.UTF_8));
        assertFalse(received.validate(signer.PublicKey()));
    }

    @ParameterizedTest @ValueSource(ints = {16, 24, 32})
    void aesGcmRoundTripAndCiphertextTamperRejection(int keySize) throws Exception {
        AlgorithmID algorithm = switch (keySize) {
            case 16 -> AlgorithmID.AES_GCM_128;
            case 24 -> AlgorithmID.AES_GCM_192;
            default -> AlgorithmID.AES_GCM_256;
        };
        byte[] key = random(keySize);
        Encrypt0Message message = new Encrypt0Message();
        message.addAttribute(HeaderKeys.Algorithm, algorithm.AsCBOR(), Attribute.PROTECTED);
        message.addAttribute(HeaderKeys.IV, CBORObject.FromObject(random(12)), Attribute.UNPROTECTED);
        message.SetContent(CONTENT);
        message.encrypt(key);
        Encrypt0Message received = (Encrypt0Message) Message.DecodeFromBytes(message.EncodeToBytes(), MessageTag.Encrypt0);
        assertArrayEquals(CONTENT, received.decrypt(key));
        CBORObject modified = CBORObject.DecodeFromBytes(message.EncodeToBytes()).Untag();
        byte[] ciphertext = modified.get(2).GetByteString();
        ciphertext[ciphertext.length - 1] ^= 1;
        modified.set(2, CBORObject.FromObject(ciphertext));
        Encrypt0Message tampered = (Encrypt0Message) Message.DecodeFromBytes(modified.EncodeToBytes(), MessageTag.Encrypt0);
        assertThrows(CoseException.class, () -> tampered.decrypt(key));
    }

    @Test void macRejectsContentTamperingAndWrongKey() throws Exception {
        byte[] key = random(32);
        MAC0Message message = new MAC0Message();
        message.addAttribute(HeaderKeys.Algorithm, AlgorithmID.HMAC_SHA_256.AsCBOR(), Attribute.PROTECTED);
        message.SetContent(CONTENT);
        message.Create(key);
        MAC0Message received = (MAC0Message) Message.DecodeFromBytes(message.EncodeToBytes(), MessageTag.MAC0);
        assertTrue(received.Validate(key));
        assertFalse(received.Validate(random(32)));
        received.SetContent("tampered content");
        assertFalse(received.Validate(key));
    }

    @Test void malformedSign1IsRejected() {
        byte[] malformed = CBORObject.NewArray().EncodeToBytes();
        assertThrows(CoseException.class, () -> Message.DecodeFromBytes(malformed, MessageTag.Sign1));
    }
}
