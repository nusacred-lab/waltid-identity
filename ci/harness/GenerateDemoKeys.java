import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.PosixFilePermissions;
import java.security.KeyPairGenerator;
import java.security.interfaces.ECPrivateKey;
import java.security.interfaces.ECPublicKey;
import java.security.spec.ECGenParameterSpec;
import java.util.Base64;
import java.math.BigInteger;

/** Fresh disposable keys using JDK cryptography; never prints key material. */
class GenerateDemoKeys {
    static String coordinate(BigInteger number) {
        byte[] encoded = number.toByteArray();
        if (encoded.length > 33 || number.signum() < 0) {
            throw new IllegalArgumentException("Unexpected P-256 coordinate");
        }
        byte[] fixed = new byte[32];
        int count = Math.min(encoded.length, fixed.length);
        System.arraycopy(encoded, encoded.length - count, fixed, fixed.length - count, count);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(fixed);
    }

    static String key() throws Exception {
        var generator = KeyPairGenerator.getInstance("EC");
        generator.initialize(new ECGenParameterSpec("secp256r1"));
        var pair = generator.generateKeyPair();
        var publicKey = (ECPublicKey) pair.getPublic();
        var privateKey = (ECPrivateKey) pair.getPrivate();
        return "{\"kty\":\"EC\",\"crv\":\"P-256\",\"x\":\""
            + coordinate(publicKey.getW().getAffineX()) + "\",\"y\":\""
            + coordinate(publicKey.getW().getAffineY()) + "\",\"d\":\""
            + coordinate(privateKey.getS()) + "\"}";
    }

    public static void main(String[] args) throws Exception {
        Path output = Path.of(args[0]);
        Files.createFile(output, PosixFilePermissions.asFileAttribute(
            PosixFilePermissions.fromString("rw-------")));
        Files.writeString(output, "{\"issuer\":" + key() + ",\"token\":" + key() + "}",
            StandardOpenOption.WRITE);
    }
}
