import _sodium from "libsodium-wrappers";

/**
 * Encrypts a secret value using the repo's public key.
 * GitHub requires NaCl sealed-box encryption (crypto_box_seal).
 *
 * @param publicKeyBase64 - base64-encoded repo public key from the Secrets API
 * @param secretValue - plaintext secret to encrypt
 * @returns base64-encoded ciphertext ready for the Secrets API
 */
export async function encryptSecret(
  publicKeyBase64: string,
  secretValue: string,
): Promise<string> {
  await _sodium.ready;
  const sodium = _sodium;

  const keyBytes = sodium.from_base64(publicKeyBase64, sodium.base64_variants.ORIGINAL);
  const messageBytes = sodium.from_string(secretValue);
  const encryptedBytes = sodium.crypto_box_seal(messageBytes, keyBytes);

  return sodium.to_base64(encryptedBytes, sodium.base64_variants.ORIGINAL);
}
