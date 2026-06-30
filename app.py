from pathlib import Path
import sys

import streamlit as st


# Allow app.py to import files from src/
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from encryption import run_secure_message_exchange


st.set_page_config(
    page_title="Quantum-Safe Communication Explorer",
    page_icon="🔐",
    layout="wide"
)


def display_figure(file_name: str, caption: str, missing_message: str):
    """
    Display a figure from the figures/ directory if it exists.
    Otherwise, show a warning message.
    """
    figure_path = PROJECT_ROOT / "figures" / file_name

    if figure_path.exists():
        st.image(
            str(figure_path),
            caption=caption,
            use_container_width=True
        )
    else:
        st.warning(missing_message)


st.title("Quantum-Safe Communication Explorer")

st.markdown(
    """
    This dashboard explores BB84 Quantum Key Distribution through protocol-level simulation,
    QBER analysis, eavesdropping detection, channel noise, error correction, privacy amplification,
    Qiskit circuit simulations, IBM Quantum hardware results, and message encryption.
    """
)


# -----------------------------
# Sidebar controls
# -----------------------------

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

st.sidebar.markdown("---")
st.sidebar.subheader("Key Processing")

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

    1. Eve = 0.00, Noise = 0.00 → should usually succeed  
    2. Eve = 0.75 → should usually abort due to high QBER  
    3. Noise = 0.18 → should usually abort if threshold is 0.11  
    4. Very small qubit count → may abort because the key is too short  
    """
)


# -----------------------------
# Session state
# -----------------------------

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if run_button:
    try:
        st.session_state.last_result = run_secure_message_exchange(
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
    except Exception as error:
        st.session_state.last_result = None
        st.error("Something went wrong while running the simulation.")
        st.exception(error)


# -----------------------------
# Tabs
# -----------------------------

live_tab, qber_tab, circuit_tab, key_tab, notes_tab = st.tabs(
    [
        "Live Simulation",
        "QBER Experiments",
        "Circuit + Hardware",
        "Key Processing",
        "Technical Notes"
    ]
)


# -----------------------------
# Live Simulation tab
# -----------------------------

with live_tab:
    st.subheader("Live BB84 Communication Simulation")

    st.markdown(
        """
        ```text
        BB84 key generation
            ↓
        QBER security check
            ↓
        Parity-based error correction
            ↓
        Privacy amplification / final key derivation
            ↓
        Message encryption and decryption
            ↓
        Abort if the channel is too noisy or unsafe
        ```
        """
    )

    if st.session_state.last_result is None:
        st.info("Use the sidebar controls and click **Run secure message exchange** to start a simulation.")

    else:
        result = st.session_state.last_result

        st.markdown("### Simulation Result")

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

        st.markdown("### Key Processing Metrics")

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

        st.markdown("### Final Key Derivation")

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


# -----------------------------
# QBER Experiments tab
# -----------------------------

with qber_tab:
    st.subheader("QBER Experiments")

    st.write(
        """
        These graphs summarize how QBER changes under eavesdropping,
        channel noise, and combined Eve-plus-noise conditions.
        """
    )

    display_figure(
        file_name="qber_vs_eve_interception.png",
        caption="QBER increases as Eve intercepts more qubits in the BB84 simulation.",
        missing_message="QBER vs Eve graph not found. Run the v0.3 QBER experiment notebook to generate it."
    )

    st.markdown("---")

    display_figure(
        file_name="qber_vs_channel_noise.png",
        caption="QBER increases as channel noise increases in the BB84 simulation.",
        missing_message="Channel noise graph not found. Run the v1.1 channel noise notebook to generate it."
    )

    st.markdown("---")

    display_figure(
        file_name="eve_noise_comparison_qber.png",
        caption="Comparison of QBER across clean, noisy, attacked, and combined scenarios.",
        missing_message="Eve vs noise comparison graph not found. Run the v1.2 comparison notebook to generate it."
    )


# -----------------------------
# Circuit + Hardware tab
# -----------------------------

with circuit_tab:
    st.subheader("Circuit and Hardware Results")

    st.write(
        """
        These results connect the protocol-level BB84 simulator to Qiskit circuits,
        noisy Qiskit Aer simulation, and selected IBM Quantum hardware runs.
        """
    )

    display_figure(
        file_name="qiskit_bb84_basis_results.png",
        caption="Qiskit simulation of BB84 measurement behavior across basis choices.",
        missing_message="Qiskit BB84 graph not found. Run the v0.6 Qiskit BB84 notebook to generate it."
    )

    st.markdown("---")

    display_figure(
        file_name="qiskit_noise_comparison.png",
        caption="Comparison of ideal and noisy BB84 circuit simulations using Qiskit Aer.",
        missing_message="Qiskit noise comparison graph not found. Run the v1.4 Qiskit noise notebook to generate it."
    )

    st.markdown("---")

    display_figure(
        file_name="ibm_hardware_comparison.png",
        caption="Selected BB84 circuits run on IBM Quantum hardware.",
        missing_message="IBM hardware graph not found. Run the v1.5 IBM hardware notebook to generate it."
    )


# -----------------------------
# Key Processing tab
# -----------------------------

with key_tab:
    st.subheader("Key Processing Experiments")

    st.write(
        """
        These experiments study the tradeoffs involved in turning sifted BB84 keys
        into usable final keys for message encryption.
        """
    )

    st.markdown("### Error Correction Parameter Sweep")

    display_figure(
        file_name="error_correction_success_rate.png",
        caption="Success rate of parity-based error correction across block sizes and correction passes.",
        missing_message="Error correction success-rate graph not found. Run the v1.6 error-correction sweep notebook to generate it."
    )

    display_figure(
        file_name="error_correction_parity_checks.png",
        caption="Average number of parity checks required across block sizes and correction passes.",
        missing_message="Error correction parity-check graph not found. Run the v1.6 error-correction sweep notebook to generate it."
    )

    st.markdown("---")

    st.markdown("### Privacy Amplification Parameter Sweep")

    display_figure(
        file_name="privacy_amplification_success_rate.png",
        caption="Message success rate across privacy compression ratios and message lengths.",
        missing_message="Privacy amplification success-rate graph not found. Run the v1.7 privacy amplification sweep notebook to generate it."
    )

    display_figure(
        file_name="privacy_amplification_key_capacity.png",
        caption="Final key capacity compared with message bit requirements.",
        missing_message="Privacy amplification key-capacity graph not found. Run the v1.7 privacy amplification sweep notebook to generate it."
    )


# -----------------------------
# Technical Notes tab
# -----------------------------

with notes_tab:
    st.subheader("Technical Notes")

    st.markdown(
        """
        This dashboard combines two kinds of outputs:

        1. **Live protocol-level simulation**  
           The sidebar controls run the BB84 communication pipeline directly.

        2. **Saved experiment results**  
           The graphs are generated from notebooks and displayed here as saved figures.
        """
    )

    st.markdown("### Current Pipeline")

    st.markdown(
        """
        ```text
        BB84 key generation
            ↓
        Eve attack model + channel noise model
            ↓
        QBER calculation
            ↓
        Parity-based error correction
            ↓
        Privacy amplification
            ↓
        Final key derivation
            ↓
        Message encryption/decryption
        ```
        """
    )

    st.markdown("### Circuit and Hardware Experiments")

    st.write(
        "The Qiskit and IBM Quantum results are generated separately from the notebooks. "
        "IBM Quantum hardware jobs are not run from the public dashboard."
    )

    with st.expander("Technical assumptions"):
        st.write(
            "This project is a simulation and analysis platform for BB84-style quantum key distribution. "
            "The live simulation models QBER checks, parity-based correction, privacy amplification, "
            "and XOR-based message encryption."
        )
        st.write(
            "Real QKD systems require authenticated channels, hardware calibration, robust reconciliation, "
            "privacy amplification, key management, and production cryptographic engineering."
        )