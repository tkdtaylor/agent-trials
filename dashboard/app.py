import streamlit as st

from dashboard.helpers import compute_side_by_side, load_results

st.set_page_config(page_title="Armor Eval Dashboard", layout="wide")
st.title("Armor Eval — Benchmark Results")

results_path = st.sidebar.text_input("Results JSON path", value="")

if not results_path:
    st.info("Enter a results JSON file path in the sidebar to load benchmark results.")
    st.stop()

try:
    summary = load_results(results_path)
except FileNotFoundError:
    st.error(f"File not found: {results_path}")
    st.stop()
except Exception as e:
    st.error(f"Failed to load results: {e}")
    st.stop()

# --- Summary metrics ---
st.header("Summary")
sides = compute_side_by_side(summary)
col_armor, col_bare = st.columns(2)

with col_armor:
    st.subheader("With Armor")
    wa = sides["with_armor"]
    st.metric("Detection rate", f"{wa.get('detection_rate', 0):.1%}")
    st.metric("False positive rate", f"{wa.get('false_positive_rate', 0):.1%}")
    st.metric("Avg latency (ms)", f"{wa.get('avg_latency_ms', 0):.1f}")

with col_bare:
    st.subheader("Without Armor")
    na = sides["without_armor"]
    st.metric("Detection rate", f"{na.get('detection_rate', 0):.1%}")
    st.metric("False positive rate", f"{na.get('false_positive_rate', 0):.1%}")
    st.metric("Avg latency (ms)", f"{na.get('avg_latency_ms', 0):.1f}")

overhead = summary.get("latency_overhead_ms", 0)
st.metric("Latency overhead (ms)", f"{overhead:.1f}")

# --- Per-attack outcome table ---
st.header("Per-attack results")
raw_results = summary.get("results", [])

if not raw_results:
    st.write("No per-attack results in this summary.")
else:
    st.dataframe(raw_results, use_container_width=True)

# --- Trace viewer ---
st.header("Trace viewer")
if raw_results:
    for i, r in enumerate(raw_results):
        label = (
            f"{r.get('attack_id', i)} — {r.get('attack_name', '')} ({'armored' if r.get('armor_active') else 'bare'})"
        )
        with st.expander(label):
            st.json(r)
