import os
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def generate_architecture_diagram(output_path: str = "architecture/system_architecture.png"):
    """Generate a clean, high-resolution architecture diagram PNG for the MVP and scalable production."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    fig.patch.set_facecolor('#0B0F19')
    ax.set_facecolor('#0B0F19')

    # Title & Subtitle
    plt.text(0.5, 0.95, "CloudScale AI: Autonomous Sales Voice Agent Architecture",
             color='#FFFFFF', fontsize=18, fontweight='bold', ha='center', transform=ax.transAxes)
    plt.text(0.5, 0.91, "End-to-End Pipeline: Voice/Text Ingestion -> RAG -> Tool-Calling Agent -> CRM & Calendar",
             color='#94A3B8', fontsize=11, ha='center', transform=ax.transAxes)

    # Box styles
    client_box = dict(boxstyle="round,pad=0.5", facecolor='#1E293B', edgecolor='#38BDF8', linewidth=2)
    core_box = dict(boxstyle="round,pad=0.5", facecolor='#1E293B', edgecolor='#3B82F6', linewidth=2)
    ai_box = dict(boxstyle="round,pad=0.5", facecolor='#1E1B4B', edgecolor='#8B5CF6', linewidth=2)
    data_box = dict(boxstyle="round,pad=0.5", facecolor='#064E3B', edgecolor='#10B981', linewidth=2)
    prod_box = dict(boxstyle="round,pad=0.5", facecolor='#451A03', edgecolor='#F59E0B', linewidth=2, linestyle='--')

    # Draw Nodes
    # 1. Client Layer
    ax.text(0.08, 0.70, "Client Layer\n(Streamlit UI / WebApp)\n• Mic (st.audio_input)\n• Text Chat & Dashboard",
            ha="center", va="center", color="#F8FAFC", fontsize=10, bbox=client_box, transform=ax.transAxes)

    # 2. Gateway / Load Balancer
    ax.text(0.25, 0.70, "Gateway\n(FastAPI Server)\n• REST & Audio Endpoints\n• CORS & Session Router",
            ha="center", va="center", color="#F8FAFC", fontsize=10, bbox=core_box, transform=ax.transAxes)

    # 3. AI Core (Speech, LLM, TTS)
    ax.text(0.48, 0.78, "Gemini STT\n(gemini-2.5-flash)\n• Speech-to-Text\n• Language Detection",
            ha="center", va="center", color="#EDE9FE", fontsize=9, bbox=ai_box, transform=ax.transAxes)

    ax.text(0.48, 0.60, "Autonomous AI Agent\n(Gemini 2.5 Flash / Demo)\n• Context Memory (10 turns)\n• Tool Calling & Sentiment\n• Lead Qualification Engine",
            ha="center", va="center", color="#EDE9FE", fontsize=9, bbox=ai_box, transform=ax.transAxes)

    ax.text(0.48, 0.42, "Edge-TTS Engine\n(Microsoft Neural Voices)\n• en-US-JennyNeural\n• hi-IN-SwaraNeural",
            ha="center", va="center", color="#EDE9FE", fontsize=9, bbox=ai_box, transform=ax.transAxes)

    # 4. Knowledge Base & RAG
    ax.text(0.72, 0.78, "Simple RAG Pipeline\n• company_info.txt\n• Gemini Embeddings\n• Cosine Similarity (Top-3)",
            ha="center", va="center", color="#ECFDF5", fontsize=9, bbox=data_box, transform=ax.transAxes)

    # 5. Database & Calendar
    ax.text(0.72, 0.50, "SQLite Database\n(SQLAlchemy ORM)\n• Leads & Scores (0-100)\n• Calls & Latency\n• Double-booking Lock",
            ha="center", va="center", color="#ECFDF5", fontsize=9, bbox=data_box, transform=ax.transAxes)

    # 6. CRM & Integrations
    ax.text(0.90, 0.50, "CRM Webhook\n& .ics Invites\n• Mock CRM Receiver\n• HubSpot / Zoho ready\n• iCalendar file generator",
            ha="center", va="center", color="#ECFDF5", fontsize=9, bbox=data_box, transform=ax.transAxes)

    # 7. Production Scale-Up (Not Implemented / Future Scale)
    ax.text(0.50, 0.16, "PRODUCTION SCALE-UP INFRASTRUCTURE (Proposed for 100,000 Concurrent Calls)\n"
                        "• Redis Cache & Rate Limiting    • Celery / RabbitMQ Event Queue    • WebRTC / WebSocket Audio Streaming\n"
                        "• Managed Vector DB (Qdrant/Pinecone)    • AWS RDS PostgreSQL + Read Replicas    • Prometheus/Grafana APM",
            ha="center", va="center", color="#FEF3C7", fontsize=9.5, bbox=prod_box, transform=ax.transAxes)

    # Draw Arrows
    arrow_props = dict(arrowstyle="->", color="#38BDF8", lw=2)
    ax.annotate("", xy=(0.17, 0.70), xytext=(0.33, 0.70), arrowprops=dict(arrowstyle="<->", color="#38BDF8", lw=2), xycoords='axes fraction')
    ax.annotate("", xy=(0.33, 0.72), xytext=(0.40, 0.78), arrowprops=arrow_props, xycoords='axes fraction')
    ax.annotate("", xy=(0.40, 0.78), xytext=(0.40, 0.65), arrowprops=arrow_props, xycoords='axes fraction')
    ax.annotate("", xy=(0.33, 0.60), xytext=(0.38, 0.60), arrowprops=arrow_props, xycoords='axes fraction')
    ax.annotate("", xy=(0.58, 0.60), xytext=(0.64, 0.76), arrowprops=dict(arrowstyle="<->", color="#8B5CF6", lw=2), xycoords='axes fraction')
    ax.annotate("", xy=(0.58, 0.58), xytext=(0.64, 0.50), arrowprops=arrow_props, xycoords='axes fraction')
    ax.annotate("", xy=(0.48, 0.52), xytext=(0.48, 0.47), arrowprops=arrow_props, xycoords='axes fraction')
    ax.annotate("", xy=(0.40, 0.42), xytext=(0.20, 0.65), arrowprops=arrow_props, xycoords='axes fraction')
    ax.annotate("", xy=(0.80, 0.50), xytext=(0.83, 0.50), arrowprops=arrow_props, xycoords='axes fraction')

    # Legend at bottom
    ax.text(0.10, 0.04, " Blue/Purple: Implemented MVP Core Pipeline", color="#38BDF8", fontsize=9, transform=ax.transAxes)
    ax.text(0.55, 0.04, " Orange (Dashed): Production Scale-Up (Design Plan for 100k Users)", color="#F59E0B", fontsize=9, transform=ax.transAxes)

    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Architecture diagram generated: {output_path}")


if __name__ == "__main__":
    generate_architecture_diagram()
