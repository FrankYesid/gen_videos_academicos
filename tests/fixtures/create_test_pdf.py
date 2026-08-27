"""Create a simple test PDF for testing the upload functionality."""
import fitz  # PyMuPDF

def create_test_pdf(output_path: str) -> None:
    """Create a simple test PDF with academic content."""
    doc = fitz.open()  # new document
    
    # Add a page
    page = doc.new_page()
    
    # Add title
    page.insert_text((50, 50), "Introduction to Machine Learning", fontsize=20, fontname="helv")
    
    # Add content
    content = """
Machine learning is a subset of artificial intelligence that focuses on building systems that can learn from data. The primary goal is to enable computers to learn automatically without human intervention or assistance and adjust actions accordingly.

Key Concepts:

1. Supervised Learning: The algorithm learns from labeled training data and makes predictions.
2. Unsupervised Learning: The algorithm finds patterns in unlabeled data.
3. Reinforcement Learning: The algorithm learns through trial and error by receiving rewards or penalties.

Applications:

- Image recognition
- Natural language processing
- Recommendation systems
- Fraud detection
- Medical diagnosis

This course provides a comprehensive introduction to these concepts and their practical applications in modern technology.
"""
    
    # Add content text (wrap it manually)
    y_position = 100
    for line in content.split('\n'):
        if line.strip():
            page.insert_text((50, y_position), line.strip(), fontsize=12, fontname="helv")
            y_position += 20
    
    # Save the PDF
    doc.save(output_path)
    doc.close()
    print(f"Test PDF created at: {output_path}")

if __name__ == "__main__":
    import os
    fixtures_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(fixtures_dir, "sample_course.pdf")
    create_test_pdf(pdf_path)