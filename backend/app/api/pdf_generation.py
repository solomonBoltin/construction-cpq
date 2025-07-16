from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session
import logging

from app.database import get_session
from app.services.pdf_generator import PDFGenerator

router = APIRouter(prefix="/pdf", tags=["PDF Generation"])
logger = logging.getLogger(__name__)


def get_pdf_generator(session: Session = Depends(get_session)) -> PDFGenerator:
    return PDFGenerator(session=session)


@router.get("/quotes/{quote_id}")
def generate_quote_pdf(
    quote_id: int,
    pdf_generator: PDFGenerator = Depends(get_pdf_generator),
):
    """Generate and return a PDF for a quote."""
    try:
        # Generate the PDF
        pdf_bytes = pdf_generator.generate_quote_pdf(quote_id)
        
        # Return the PDF as a response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=quote_{quote_id}.pdf"
            }
        )
        
    except ValueError as e:
        logger.error(f"ValueError generating PDF for quote {quote_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating PDF for quote {quote_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the PDF")


@router.get("/quotes/{quote_id}/inline")
def generate_quote_pdf_inline(
    quote_id: int,
    pdf_generator: PDFGenerator = Depends(get_pdf_generator),
):
    """Generate and return a PDF for a quote for inline viewing."""
    try:
        # Generate the PDF
        pdf_bytes = pdf_generator.generate_quote_pdf(quote_id)
        
        # Return the PDF as a response for inline viewing
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=quote_{quote_id}.pdf"
            }
        )
        
    except ValueError as e:
        logger.error(f"ValueError generating PDF for quote {quote_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating PDF for quote {quote_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the PDF")