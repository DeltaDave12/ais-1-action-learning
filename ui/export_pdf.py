from fpdf import FPDF

def export_conversation_to_pdf(conversation, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "Conversation Export", ln=True, align="C")
    pdf.ln(10)

    for message in conversation:
        role = message.get("role", "")
        content = message.get("content", "")
        if role == "user":
            pdf.set_text_color(0, 0, 128)
            pdf.cell(0, 10, "User:", ln=True)
        elif role == "assistant":
            pdf.set_text_color(0, 128, 0)
            pdf.cell(0, 10, "Assistant:", ln=True)
        else:
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, f"{role.capitalize()}:", ln=True)
        pdf.set_text_color(0, 0, 0)
        # Split content into lines for better formatting
        for line in content.splitlines():
            pdf.multi_cell(0, 8, line)
        pdf.ln(4)

    pdf.output(filename) 