# Architecture Diagram — Cryptographic Pipeline Flow

**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Cryptographic Pipeline Flowchart

```mermaid
flowchart TD
    subgraph SenderPipeline["Sender Cryptographic Pipeline (Branch A)"]
        OriginalFile["Original Plaintext Payload"]
        
        CalcOrigDigest["1. Calculate SHA-256 Digest"]
        GenDEK["2. Generate Random 256-bit DEK (os.urandom)"]
        WrapDEK["3. Key Wrap DEK with Master KEK (RFC 3394)"]
        GenNonce["4. Generate 96-bit Random Nonce (os.urandom)"]
        ConstructAAD["5. Construct AAD (Protocol, IDs, Size)"]
        AESGCMEncrypt["6. AES-256-GCM Encrypt(DEK, Nonce, Plaintext, AAD)"]
        
        OriginalFile --> CalcOrigDigest
        OriginalFile --> AESGCMEncrypt
        GenDEK --> WrapDEK
        GenDEK --> AESGCMEncrypt
        GenNonce --> AESGCMEncrypt
        ConstructAAD --> AESGCMEncrypt
        
        EnvelopeConstruct["7. Assemble Transfer Envelope (v1)"]
        CalcOrigDigest --> EnvelopeConstruct
        WrapDEK --> EnvelopeConstruct
        GenNonce --> EnvelopeConstruct
        ConstructAAD --> EnvelopeConstruct
        AESGCMEncrypt -->|Ciphertext + 128-bit Tag| EnvelopeConstruct
    end

    subgraph NetworkTransit["Network Transit (WireGuard Tunnel)"]
        WireGuardEncapsulation["WireGuard VPN (ChaCha20-Poly1305 Encapsulation)"]
    end

    subgraph ReceiverPipeline["Receiver Cryptographic Pipeline (Branch B)"]
        EnvelopeReceived["Received Transfer Envelope (v1)"]
        UnwrapDEK["8. Unwrap DEK using Master KEK"]
        ValidateTagAndDecrypt["9. AES-256-GCM Authenticate Tag & Decrypt"]
        QuarantineBranch["QUARANTINE & AUDIT ALERT (No Plaintext Released)"]
        CalcRecvDigest["10. Calculate SHA-256 on Recovered Plaintext"]
        VerifyDigestMatch{"11. Compare Recv Digest == Orig Digest?"}
        VerifiedPlaintext["12. Verified Plaintext Delivered to User"]
        
        EnvelopeReceived --> UnwrapDEK
        EnvelopeReceived --> ValidateTagAndDecrypt
        UnwrapDEK --> ValidateTagAndDecrypt
        
        ValidateTagAndDecrypt -->|Tag Mismatch / Tampered| QuarantineBranch
        ValidateTagAndDecrypt -->|Tag Validated| CalcRecvDigest
        CalcRecvDigest --> VerifyDigestMatch
        
        VerifyDigestMatch -->|Mismatch| QuarantineBranch
        VerifyDigestMatch -->|Match| VerifiedPlaintext
    end

    EnvelopeConstruct --> WireGuardEncapsulation
    WireGuardEncapsulation --> EnvelopeReceived
```

---

## 2. Cryptographic Formulae & Invariants

1. **Original Digest Calculation**:
   $$\text{Digest}_{\text{orig}} = \text{SHA-256}(\text{Plaintext})$$
2. **Key Encryption Key (KEK) Wrapping**:
   $$\text{WrappedDEK} = \text{AES-KeyWrap}_{\text{KEK}}(\text{DEK}_{\text{ephemeral}})$$
3. **AEAD Encryption & Tag Generation**:
   $$(\text{Ciphertext}, \text{Tag}_{128}) = \text{AES-256-GCM-Encrypt}(\text{Key}=\text{DEK}, \text{IV}=\text{Nonce}_{96}, \text{PT}=\text{Plaintext}, \text{AAD})$$
4. **Post-Decryption Verification Guard**:
   $$\text{Assert}(\text{AES-256-GCM-Decrypt}(\text{DEK}, \text{Nonce}, \text{Ciphertext}, \text{AAD}, \text{Tag}) == \text{Plaintext})$$
   $$\text{Assert}(\text{SHA-256}(\text{Plaintext}) == \text{Digest}_{\text{orig}})$$
