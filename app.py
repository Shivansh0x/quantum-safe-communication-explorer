from pathlib import Path
import sys

import streamlit as st


# Allow app.py to import files from src/
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.append(str(SRC_PATH))

from encryption import run_secure_message_exchange


st.set_page_config(
    page_title="Quantum-Safe Communication Explorer",
    page_icon="🔐",
    layout="wide"
)


st.title("Quantum-Safe Communication Explorer")
st.markdown(
    """
    This dashboard demonstrates a simplified quantum-safe communication flow using the BB84 
    Quantum Key Distribution protocol.

    The simulation generates a shared key between Alice and Bob, checks the Quantum Bit Error Rate,
    and only encrypts the message if the channel appears safe.
    """
)


st.sidebar.header("Simulation Controls")

message = st.sidebar.text_area(
    "Message to send",
    value="Hello quantum world",
    height=100
)

n_qubits = st.sidebar.slider(
    "Number of BB84 qubits",
    min_value=100,
    max_value=20000,
    value=5000,
    step=100
)

eve_intercept_prob = st.sidebar.slider(
    "Eve interception probability",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.05
)

channel_noise_prob = st.sidebar.slider(
    "Channel noise probability",
    min_value=0.0,
    max_value=0.20,
    value=0.0,
    step=0.01
)

qber_threshold = st.sidebar.slider(
    "QBER safety threshold",
    min_value=0.0,
    max_value=0.30,
    value=0.11,
    step=0.01
)

use_error_correction = st.sidebar.checkbox(
    "Use parity-based error correction",
    value=True
)

error_correction_passes = st.sidebar.slider(
    "Error-correction passes",
    min_value=1,
    max_value=10,
    value=5,
    step=1
)

error_correction_block_size = st.sidebar.selectbox(
    "Error-correction block size",
    options=[8, 16, 32, 64],
    index=1
)

use_privacy_amplification = st.sidebar.checkbox(
    "Use privacy amplification",
    value=True
)

privacy_compression_ratio = st.sidebar.slider(
    "Privacy compression ratio",
    min_value=0.25,
    max_value=0.90,
    value=0.50,
    step=0.05
)

run_button = st.sidebar.button("Run secure message exchange")


st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Suggested tests**

    1. Eve = 0.00 → should usually succeed  
    2. Eve = 0.75 → should usually abort  
    3. Very small qubit count → may abort because the key is too short  
    """
)


st.subheader("Protocol Flow")

st.markdown(
    """
    ```text
    BB84 key generation
        ↓
    QBER security check
        ↓
    Message encryption using generated key
        ↓
    Message decryption by Bob
        ↓
    Abort if attack/noise is detected
    ```
    """
)


if run_button:
    try:
        result = run_secure_message_exchange(
            message=message,
            n_qubits=n_qubits,
            eve_intercept_prob=eve_intercept_prob,
            channel_noise_prob=channel_noise_prob,
            qber_threshold=qber_threshold,
            use_error_correction=use_error_correction,
            error_correction_block_size=error_correction_block_size,
            error_correction_passes=error_correction_passes,
            use_privacy_amplification=use_privacy_amplification,
            privacy_compression_ratio=privacy_compression_ratio
        )

        st.subheader("Simulation Result")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Status", result["status"].upper())

        with col2:
            st.metric("QBER", f"{result['qber']:.4f}")

        with col3:
            st.metric("QBER Threshold", f"{result['qber_threshold']:.2f}")

        with col4:
            st.metric("Eve Interception", f"{result['eve_intercept_prob']:.2f}")
        
        with col5:
            st.metric("Channel Noise", f"{result['channel_noise_prob']:.2f}")

        st.markdown("### Decision")

        if result["status"] == "success":
            st.success(result["reason"])
        else:
            st.error(result["reason"])

        st.markdown("### Key Information")

        key_col1, key_col2, key_col3, key_col4 = st.columns(4)

        with key_col1:
            st.metric("Message Bits", result["message_bits_required"])

        with key_col2:
            st.metric("Raw Key Length", result["raw_alice_key_length"])

        with key_col3:
            st.metric("Reconciled Length", result["reconciled_key_length"])

        with key_col4:
            st.metric("Final Key Bits", result["alice_key_length"])

        ec_col1, ec_col2, ec_col3, ec_col4 = st.columns(4)

        with ec_col1:
            st.metric("Raw Mismatches", result["raw_mismatches"])

        with ec_col2:
            st.metric("Final Mismatches", result["final_mismatches"])

        with ec_col3:
            st.metric("Corrections", result["corrections_applied"])

        with ec_col4:
            st.metric("Parity Checks", result["parity_checks"])

        st.markdown("### Key Derivation")

        if result["privacy_amplification_used"]:
            st.write(
                f"Privacy amplification enabled with compression ratio "
                f"{result['privacy_compression_ratio']:.2f}."
            )

            if result["final_key_fingerprint"]:
                st.write("Final key fingerprint:")
                st.code(result["final_key_fingerprint"], language="text")
        else:
            st.write("Privacy amplification disabled.")

        st.markdown("### Message Exchange")

        st.write("**Original message:**")
        st.code(result["message"], language="text")

        if result["status"] == "success":
            st.write("**Ciphertext bits:**")
            st.code(result["ciphertext_display"], language="text")

            st.write("**Decrypted message:**")
            st.code(result["decrypted_message"], language="text")
        else:
            st.warning("Message transmission was aborted, so no ciphertext was sent.")

        with st.expander("Show technical details"):
            st.write("This simulation uses the BB84 protocol to generate a shared key.")
            st.write(
                "If QBER is above the selected threshold, the system assumes possible "
                "eavesdropping or excessive noise and aborts communication."
            )
            st.write(
                "If Alice and Bob's keys do not match exactly, the system also aborts. "
                "This version does not yet implement error correction or privacy amplification."
            )

    except Exception as error:
        st.error("Something went wrong while running the simulation.")
        st.exception(error)


st.markdown("---")
st.subheader("QBER Experiment Result")

figure_path = PROJECT_ROOT / "figures" / "qber_vs_eve_interception.png"

if figure_path.exists():
    st.image(
        str(figure_path),
        caption="QBER increases as Eve intercepts more qubits in the BB84 simulation."
    )
else:
    st.warning(
        "QBER graph not found. Run the v0.3 QBER experiment notebook to generate the graph."
    )

st.markdown("---")
st.subheader("Qiskit Circuit-Based BB84 Result")

qiskit_figure_path = PROJECT_ROOT / "figures" / "qiskit_bb84_basis_results.png"

if qiskit_figure_path.exists():
    st.image(
        str(qiskit_figure_path),
        caption="Qiskit simulation of BB84 measurement behavior across basis choices."
    )
else:
    st.warning(
        "Qiskit BB84 graph not found. Run the v0.6 Qiskit BB84 notebook to generate the graph."
    )

st.markdown("---")
st.subheader("Channel Noise Experiment Result")

noise_figure_path = PROJECT_ROOT / "figures" / "qber_vs_channel_noise.png"

if noise_figure_path.exists():
    st.image(
        str(noise_figure_path),
        caption="QBER increases as channel noise increases in the BB84 simulation."
    )
else:
    st.warning(
        "Channel noise graph not found. Run the v1.1 channel noise notebook to generate the graph."
    )

st.markdown("---")
st.subheader("Eve vs Channel Noise Comparison")

comparison_figure_path = PROJECT_ROOT / "figures" / "eve_noise_comparison_qber.png"

if comparison_figure_path.exists():
    st.image(
        str(comparison_figure_path),
        caption="Comparison of QBER across clean, noisy, attacked, and combined scenarios."
    )
else:
    st.warning(
        "Eve vs noise comparison graph not found. Run the v1.2 comparison notebook to generate the graph."
    )

st.markdown("---")
st.subheader("Qiskit Aer Noise Model Result")

qiskit_noise_figure_path = PROJECT_ROOT / "figures" / "qiskit_noise_comparison.png"

if qiskit_noise_figure_path.exists():
    st.image(
        str(qiskit_noise_figure_path),
        caption="Comparison of ideal and noisy BB84 circuit simulations using Qiskit Aer."
    )
else:
    st.warning(
        "Qiskit noise comparison graph not found. Run the v1.4 Qiskit noise notebook to generate the graph."
    )

st.markdown("---")
st.subheader("Security Note")

with st.expander("Technical assumptions"):
    st.write(
        "This dashboard is a simulation of the BB84 workflow. "
        "The implementation includes BB84 key generation, QBER checks, "
        "parity-based correction, privacy amplification, and XOR-based message encryption."
    )
    st.write(
        "Production QKD systems require authenticated channels, hardware-level considerations, "
        "robust reconciliation, privacy amplification, and standard cryptographic engineering."
    )