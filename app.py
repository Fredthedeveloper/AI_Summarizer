# app.py
from flask import Flask, render_template, request, redirect, url_for
from transformers import BartForConditionalGeneration, BartTokenizer
import fitz  # PyMuPDF for PDFs
import docx  # python-docx for DOCX
import requests

app = Flask(__name__)

model_name = "facebook/bart-large-cnn"
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)

max_length = 1024  # Set the desired maximum number of tokens for each chunk
max_new_tokens = 200  # Set the desired maximum number of new tokens for the summary


def summarize_text(text):
    # Split the input text into chunks
    chunks = [text[i : i + max_length] for i in range(0, len(text), max_length)]

    # Summarize each chunk
    summaries = []
    for chunk in chunks:
        input_ids = tokenizer(
            chunk, return_tensors="pt", max_length=max_length, truncation=True
        )["input_ids"]
        summary_ids = model.generate(input_ids, max_new_tokens=max_new_tokens)
        summarized_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summaries.append(summarized_text)

    # Combine the summaries to form the final summarized text
    summarized_text = " ".join(summaries)
    return summarized_text


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            input_text = request.form["input_text"]
            summarized_text = summarize_text(input_text)
            return render_template(
                "index.html", input_text=input_text, summarized_text=summarized_text
            )
        except requests.exceptions.RequestException:
            error_message = "Network error. Please check your internet connection."
            return render_template("index.html", error_message=error_message)
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        try:
            file = request.files["file"]
            if file:
                filename = file.filename.lower()
                if filename.endswith(".pdf"):
                    input_text = extract_text_from_pdf(file)
                elif filename.endswith(".docx"):
                    input_text = extract_text_from_docx(file)
                else:
                    return render_template(
                        "upload.html",
                        error_message="Unsupported file format. Please upload a PDF or DOCX file.",
                    )

                summarized_text = summarize_text(input_text)
                return render_template(
                    "upload.html",
                    input_text=input_text,
                    summarized_text=summarized_text,
                )
        except requests.exceptions.RequestException:
            error_message = "Network error. Please check your internet connection."
            return render_template("upload.html", error_message=error_message)

    return render_template("upload.html")


def extract_text_from_pdf(file):
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in pdf_document:
        text += page.get_text()
    pdf_document.close()
    return text


def extract_text_from_docx(file):
    doc = docx.Document(file)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


if __name__ == "__main__":
    app.run(debug=True)
