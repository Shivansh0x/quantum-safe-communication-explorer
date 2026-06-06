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

qber_threshold = st.sidebar.slider(
    "QBER safety threshold",
    min_value=0.0,
    max_value=0.30,
    value=0.11,
    step=0.01
)

use_simplified_reconciliation = st.sidebar.checkbox(
    "Use simplified educational reconciliation",
    value=True
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
            qber_threshold=qber_threshold,
            use_simplified_reconciliation=use_simplified_reconciliation
        )

        st.subheader("Simulation Result")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Status", result["status"].upper())

        with col2:
            st.metric("QBER", f"{result['qber']:.4f}")

        with col3:
            st.metric("QBER Threshold", f"{result['qber_threshold']:.2f}")

        with col4:
            st.metric("Eve Interception", f"{result['eve_intercept_prob']:.2f}")

        st.markdown("### Decision")

        if result["status"] == "success":
            st.success(result["reason"])
        else:
            st.error(result["reason"])

        st.markdown("### Key Information")

        key_col1, key_col2, key_col3, key_col4 = st.columns(4)

        with key_col1:
            st.metric("Message Bits Required", result["message_bits_required"])

        with key_col2:
            st.metric("Raw Key Length", result["raw_alice_key_length"])

        with key_col3:
            st.metric("Final Key Length", result["alice_key_length"])

        with key_col4:
            st.metric("Bits Removed", result["mismatched_bits_removed"])
        
        if result["reconciliation_used"]:
            st.info(
                "Simplified educational reconciliation was used. "
                "Mismatched key positions were removed in the simulation before encryption."
            )
        else:
            st.warning(
                "Reconciliation is disabled. Alice and Bob's raw keys must match exactly."
    )

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
st.subheader("Security Note")

st.info(
    """
    This project is an educational simulation, not production cryptographic software.

    The current encryption layer uses XOR as a one-time-pad style demonstration.
    The simplified reconciliation option removes mismatched key positions using simulation-only access.
    Real BB84 requires authenticated public discussion, error correction, privacy amplification,
    proper key management, and carefully implemented cryptographic standards.
    """
)