"""
ElectroMart India — Architecture Diagram Generator
Generates architecture/system_architecture.png using Matplotlib.
Clean, modern, high-resolution visual layout.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

ARCH_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PNG = os.path.join(ARCH_DIR, "system_architecture.png")


def draw_architecture():
    fig, ax = plt.subplots(figsize=(14, 9), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")

    # Background
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # Title
    ax.text(7, 8.5, "ElectroMart India — Autonomous AI Sales Voice Agent Architecture",
            fontsize=15, weight="bold", ha="center", color="#0F172A")
    ax.text(7, 8.15, "Multilingual Voice Advisory • RAG Product Catalog • Deterministic Lead Scoring • SQLite CRM",
            fontsize=10, ha="center", color="#475569")

    # Helper function to draw rounded boxes
    def draw_box(x, y, w, h, title, subtitle, bg_color, border_color):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.2,rounding_size=0.15",
            facecolor=bg_color, edgecolor=border_color, linewidth=1.5
        )
        ax.add_patch(box)
        ax.text(x + w / 2, y + h * 0.65, title, fontsize=10.5, weight="bold", ha="center", va="center", color="#0F172A")
        ax.text(x + w / 2, y + h * 0.32, subtitle, fontsize=8.2, ha="center", va="center", color="#475569")

    # 1. Client Layer (Top)
    draw_box(1.0, 6.7, 3.4, 0.95, "🖥️ Streamlit Frontend UI", "3 Tabs • Live Chat • CRM • BI Insights", "#EFF6FF", "#2563EB")
    draw_box(5.3, 6.7, 3.4, 0.95, "🎙️ Speech-to-Text (STT)", "OpenAI Whisper / Free Web Speech", "#F0FDF4", "#16A34A")
    draw_box(9.6, 6.7, 3.4, 0.95, "🗣️ Text-to-Speech (TTS)", "Edge-TTS (en-IN / te-IN / kn-IN)", "#FAF5FF", "#9333EA")

    # 2. API Gateway & Controller Layer (Middle-Top)
    draw_box(4.5, 5.1, 5.0, 1.0, "⚡ FastAPI REST API Gateway", "Endpoints: /call/text, /call/audio, /products, /leads, /appointments", "#FEF3C7", "#D97706")

    # 3. Core AI & Reasoning Layer (Middle)
    draw_box(0.8, 3.1, 3.6, 1.25, "📚 TF-IDF & NumPy RAG", "8 Knowledge Base Docs\nCosine Relevance Retrieval", "#F8FAFC", "#64748B")
    draw_box(5.2, 3.1, 3.6, 1.25, "🤖 AI Sales Agent (Anya)", "OpenAI GPT-4o-mini / Demo\n+ Context & 10-Turn Memory", "#EFF6FF", "#2563EB")
    draw_box(9.6, 3.1, 3.6, 1.25, "🎯 Recommendation Engine", "data/products.csv Source of Truth\nBudget & Spec Matching", "#F0FDF4", "#16A34A")

    # 4. Analytics & Validation Engines (Middle-Bottom)
    draw_box(0.8, 1.4, 3.6, 1.1, "📊 Sentiment Engine", "Regex Word Boundary Tokenizer\nEscalation Alert Guard", "#FFF7ED", "#EA580C")
    draw_box(5.2, 1.4, 3.6, 1.1, "🎯 BANT Qualification", "Pydantic Models • 0-100 Score\nHOT / WARM / COLD Bands", "#FDF2F8", "#DB2777")
    draw_box(9.6, 1.4, 3.6, 1.1, "📅 Appointment Engine", "Conflict Prevention Lock\nRFC 5545 .ICS File Generator", "#ECFEFF", "#0891B2")

    # 5. Persistence Layer (Bottom)
    draw_box(3.5, 0.2, 7.0, 0.85, "🗄️ SQLite Database & CRM (electromart.db)", "Customers • Leads • Calls • Messages • Appointments • Call Summaries", "#F1F5F9", "#475569")

    # Arrows connecting layers
    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            label, xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color="#475569", lw=1.3, mutation_scale=12),
            ha="center", va="center", fontsize=7.5, color="#64748B"
        )

    # Connections
    draw_arrow(2.7, 6.7, 5.5, 6.1)
    draw_arrow(7.0, 6.7, 7.0, 6.1)
    draw_arrow(11.3, 6.7, 8.5, 6.1)

    draw_arrow(6.0, 5.1, 2.6, 4.35)
    draw_arrow(7.0, 5.1, 7.0, 4.35)
    draw_arrow(8.0, 5.1, 11.4, 4.35)

    draw_arrow(4.4, 3.7, 5.2, 3.7)
    draw_arrow(9.6, 3.7, 8.8, 3.7)

    draw_arrow(2.6, 3.1, 2.6, 2.5)
    draw_arrow(7.0, 3.1, 7.0, 2.5)
    draw_arrow(11.4, 3.1, 11.4, 2.5)

    draw_arrow(2.6, 1.4, 5.5, 1.05)
    draw_arrow(7.0, 1.4, 7.0, 1.05)
    draw_arrow(11.4, 1.4, 8.5, 1.05)

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Architecture diagram saved to {OUTPUT_PNG}")


if __name__ == "__main__":
    draw_architecture()
