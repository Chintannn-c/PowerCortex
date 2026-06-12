import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.core.dependencies import get_current_user

# Bypass auth for testing
app.dependency_overrides[get_current_user] = lambda: {"_id": "60d5ec4b9b1d8b2d888f4e12", "username": "admin", "email": "admin@guvnl.gov.in"}

class TestPdfReportGeneration(unittest.TestCase):

    def test_download_pdf_grid_performance(self):
        """Test GET /api/reports/download/grid-performance/pdf endpoint."""
        with TestClient(app) as client:
            response = client.get("/api/reports/download/grid-performance/pdf")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get("content-type"), "application/pdf")
            self.assertIn("content-disposition", response.headers)
            self.assertIn("attachment; filename=", response.headers["content-disposition"])
            self.assertTrue(response.headers["content-disposition"].endswith('.pdf"'))
            
            # Verify PDF content starts with PDF signature %PDF
            content = response.content
            self.assertTrue(content.startswith(b"%PDF"))
            
            # Save the file to disk for manual inspection
            output_path = os.path.join(os.path.dirname(__file__), "test_output_grid_performance.pdf")
            with open(output_path, "wb") as f:
                f.write(content)
                
            print(f"PDF Report generated and saved successfully to: {output_path}")
            self.assertGreater(len(content), 1000) # Ensure it is not empty

    def test_download_pdf_weekly_asset(self):
        """Test GET /api/reports/download/weekly-asset/pdf endpoint."""
        with TestClient(app) as client:
            response = client.get("/api/reports/download/weekly-asset/pdf")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get("content-type"), "application/pdf")
            content = response.content
            self.assertTrue(content.startswith(b"%PDF"))

    def test_download_pdf_fault_analysis(self):
        """Test GET /api/reports/download/fault-analysis/pdf endpoint."""
        with TestClient(app) as client:
            response = client.get("/api/reports/download/fault-analysis/pdf")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get("content-type"), "application/pdf")
            content = response.content
            self.assertTrue(content.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
