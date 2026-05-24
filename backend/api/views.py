"""
Django REST Framework views for FinScope AI API
Converted from FastAPI routes
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio

from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from asgiref.sync import sync_to_async, async_to_sync

# Import existing route logic
from api.routes import health, classify, plan, research, report, ingest, retrieve, analytics
from api.schemas.query import QueryRequest, ClassificationResponse
from api.schemas.plan import PlanRequest, PlanResponse
from api.schemas.research import ResearchAnalysisRequest, ResearchAnalysisResponse
from api.schemas.research_engine import ResearchRequest, ResearchResponse
from api.schemas.rag import IngestRequest, IngestResponse, RetrieveRequest, RetrieveResponse
from api.schemas.report import (
    ReportResponse, ReportListResponse, ReportExportRequest, ReportExportResponse
)
from api.schemas.analytics import DashboardResponse, MetricsSummaryResponse
from utils.logger import log
from core.models import Query, Report


# ==================== Health Endpoint ====================

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "FinScope AI API",
    })


# ==================== Root Endpoint ====================

@api_view(['GET'])
def root(request):
    """Root endpoint"""
    return Response({
        "message": "FinScope AI API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
    })


# ==================== Classification Endpoint ====================

class ClassifyView(APIView):
    """Classify query endpoint"""
    
    def post(self, request):
        """Classify a user query to determine the appropriate sector"""
        try:
            # Get query from request
            query_text = request.data.get('query')
            if not query_text:
                return Response(
                    {"detail": "Query is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create QueryRequest object
            query_request = QueryRequest(query=query_text)
            
            # Call the async classify function
            result = async_to_sync(classify.classify_query)(query_request)
            
            # Convert to dict if it's a Pydantic model
            if hasattr(result, 'dict'):
                return Response(result.dict())
            elif hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Classification endpoint error: {e}", exc_info=True)
            return Response(
                {
                    "sector": "Unknown",
                    "confidence": 0.0,
                    "reasoning": f"Classification error: {str(e)}",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== Planning Endpoint ====================

class PlanView(APIView):
    """Generate research plan endpoint"""
    
    def post(self, request):
        """Generate deep research plan for a query"""
        try:
            query_text = request.data.get('query')
            sector = request.data.get('sector', 'Unknown')
            
            if not query_text:
                return Response(
                    {"detail": "Query is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            plan_request = PlanRequest(query=query_text, sector=sector)
            result = async_to_sync(plan.create_research_plan)(plan_request)
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Planning endpoint error: {e}")
            return Response(
                {"detail": f"Internal server error during plan generation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== Research Endpoints ====================

class ResearchAnalyzeView(APIView):
    """Conduct research analysis endpoint"""
    
    def post(self, request):
        """Conduct comprehensive in-depth research analysis"""
        try:
            research_request = ResearchAnalysisRequest(**request.data)
            result = async_to_sync(research.conduct_research_analysis)(research_request)
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Research analysis error: {e}")
            return Response(
                {"detail": f"Internal server error during research analysis: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResearchStartView(APIView):
    """Start research workflow endpoint"""
    
    def post(self, request):
        """Start deep research workflow"""
        try:
            research_request = ResearchRequest(**request.data)
            # Pass Django request object (research.start_research may use it for headers, etc.)
            result = async_to_sync(research.start_research)(research_request, request)
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Research start error: {e}")
            return Response(
                {"detail": f"Internal server error during research: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class ResearchStartPDFView(APIView):
    """Start research with PDF upload endpoint"""
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Start deep research workflow with PDF file upload"""
        try:
            query = request.data.get('query')
            sector = request.data.get('sector', 'Unknown')
            pdf_file = request.FILES.get('pdf_file')
            selected_questions = request.data.get('selected_questions', '[]')
            
            if not query or not pdf_file:
                return Response(
                    {"detail": "Query and PDF file are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a mock UploadFile-like object for compatibility
            class MockUploadFile:
                def __init__(self, django_file):
                    self.filename = django_file.name
                    self.file = django_file
                    self._content = None
                
                async def read(self):
                    if self._content is None:
                        self._content = self.file.read()
                    return self._content
            
            mock_file = MockUploadFile(pdf_file)
            
            # Call the async function
            result = async_to_sync(research.start_research_with_pdf)(
                query=query,
                sector=sector,
                pdf_file=mock_file,
                selected_questions=selected_questions,
                http_request=request
            )
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Research PDF start error: {e}")
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== Report Endpoints ====================

class ReportDetailView(APIView):
    """Get and delete report by query ID"""
    
    def get(self, request, query_id):
        """Get a research report by query ID"""
        try:
            result = async_to_sync(report.get_report)(query_id)
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Get report error: {e}")
            if "not found" in str(e).lower():
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, query_id):
        """Delete a research report by query ID"""
        try:
            result = async_to_sync(report.delete_report)(query_id)
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Delete report error: {e}")
            if "not found" in str(e).lower():
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportListView(APIView):
    """List all reports"""
    
    def get(self, request):
        """List all research reports"""
        try:
            sector = request.query_params.get('sector')
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
            include_in_progress = request.query_params.get('include_in_progress', 'true').lower() == 'true'
            
            result = async_to_sync(report.list_reports)(
                sector=sector,
                limit=limit,
                offset=offset,
                include_in_progress=include_in_progress
            )
            
            if hasattr(result, 'model_dump'):
                response_data = result.model_dump()
            elif hasattr(result, 'dict'):
                response_data = result.dict()
            else:
                response_data = result
            
            # Frontend expects an array directly, not wrapped in a response object
            if isinstance(response_data, dict) and 'reports' in response_data:
                # If it's a ReportListResponse, extract the reports array
                return Response(response_data['reports'])
            elif isinstance(response_data, list):
                return Response(response_data)
            else:
                return Response(response_data)
                
        except Exception as e:
            log.error(f"List reports error: {e}", exc_info=True)
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportExportView(APIView):
    """Export report in various formats"""
    
    def post(self, request, query_id):
        """Export report as PDF, HTML, or Markdown"""
        try:
            format_type = request.data.get('format', 'pdf')
            
            # Create ReportExportRequest
            export_request = ReportExportRequest(
                query_id=query_id,
                format=format_type
            )
            
            result = async_to_sync(report.export_report)(export_request)
            
            if hasattr(result, 'model_dump'):
                response_data = result.model_dump()
            elif hasattr(result, 'dict'):
                response_data = result.dict()
            else:
                response_data = result
            
            # If it's a file path, return the file
            if 'file_path' in response_data:
                file_path = Path(response_data['file_path'])
                if file_path.exists():
                    return FileResponse(
                        open(file_path, 'rb'),
                        content_type='application/pdf' if format_type == 'pdf' else 'text/html' if format_type == 'html' else 'text/markdown',
                        filename=file_path.name
                    )
            
            return Response(response_data)
                
        except Exception as e:
            log.error(f"Export report error: {e}")
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== RAG Endpoints ====================

class IngestView(APIView):
    """Ingest document into RAG system"""
    
    def post(self, request):
        """Ingest document into RAG system"""
        try:
            ingest_request = IngestRequest(**request.data)
            result = async_to_sync(ingest.ingest_document)(ingest_request)
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Ingest error: {e}")
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RetrieveView(APIView):
    """Retrieve documents using hybrid RAG system"""
    
    def post(self, request):
        """Retrieve documents using hybrid RAG system"""
        try:
            retrieve_request = RetrieveRequest(**request.data)
            result = async_to_sync(retrieve.retrieve_documents)(retrieve_request)
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Retrieval error: {e}")
            return Response(
                {"detail": f"Internal server error during retrieval: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== Analytics Endpoints ====================

class AnalyticsDashboardView(APIView):
    """Get analytics dashboard data"""
    
    def get(self, request):
        """Get comprehensive analytics dashboard data"""
        try:
            days = int(request.query_params.get('days', 7))
            result = async_to_sync(analytics.get_dashboard)(days=days)
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Analytics dashboard error: {e}")
            return Response(
                {"detail": f"Error generating dashboard: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsMetricsView(APIView):
    """Get metrics summary"""
    
    def get(self, request):
        """Get metrics summary"""
        try:
            result = async_to_sync(analytics.get_metrics)()
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Analytics metrics error: {e}")
            return Response(
                {"detail": f"Error getting metrics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsOverviewView(APIView):
    """Get overview statistics"""
    
    def get(self, request):
        """Get overview statistics"""
        try:
            result = async_to_sync(analytics.get_overview)()
            return Response(result)
                
        except Exception as e:
            log.error(f"Analytics overview error: {e}")
            return Response(
                {"detail": f"Error getting overview: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsSectorsView(APIView):
    """Get sector distribution"""
    
    def get(self, request):
        """Get query distribution by sector"""
        try:
            result = async_to_sync(analytics.get_sector_distribution)()
            return Response(result)
                
        except Exception as e:
            log.error(f"Analytics sectors error: {e}")
            return Response(
                {"detail": f"Error getting sector distribution: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsPlanTypesView(APIView):
    """Get plan type distribution"""
    
    def get(self, request):
        """Get query distribution by plan type"""
        try:
            result = async_to_sync(analytics.get_plan_type_distribution)()
            return Response(result)
                
        except Exception as e:
            log.error(f"Analytics plan types error: {e}")
            return Response(
                {"detail": f"Error getting plan type distribution: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsToolUsageView(APIView):
    """Get tool usage statistics"""
    
    def get(self, request):
        """Get tool usage statistics"""
        try:
            result = async_to_sync(analytics.get_tool_usage)()
            return Response(result)
                
        except Exception as e:
            log.error(f"Analytics tool usage error: {e}")
            return Response(
                {"detail": f"Error getting tool usage: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsResponseTimeTrendView(APIView):
    """Get response time trend"""
    
    def get(self, request):
        """Get response time trend"""
        try:
            days = int(request.query_params.get('days', 7))
            result = async_to_sync(analytics.get_response_time_trend)(days=days)
            return Response(result)
                
        except Exception as e:
            log.error(f"Analytics response time trend error: {e}")
            return Response(
                {"detail": f"Error getting response time trend: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsDailyStatsView(APIView):
    """Get daily statistics"""
    
    def get(self, request):
        """Get daily statistics"""
        try:
            days = int(request.query_params.get('days', 7))
            result = async_to_sync(analytics.get_daily_stats)(days=days)
            return Response(result)
                
        except Exception as e:
            log.error(f"Analytics daily stats error: {e}")
            return Response(
                {"detail": f"Error getting daily stats: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsSectorPerformanceView(APIView):
    """Get sector performance"""
    
    def get(self, request):
        """Get sector performance"""
        try:
            result = async_to_sync(analytics.get_sector_performance)()
            return Response(result)
                
        except Exception as e:
            log.error(f"Analytics sector performance error: {e}")
            return Response(
                {"detail": f"Error getting sector performance: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsTopQueriesView(APIView):
    """Get top queries"""
    
    def get(self, request):
        """Get top queries"""
        try:
            limit = int(request.query_params.get('limit', 10))
            result = async_to_sync(analytics.get_top_queries)(limit=limit)
            return Response(result)
                
        except Exception as e:
            log.error(f"Analytics top queries error: {e}")
            return Response(
                {"detail": f"Error getting top queries: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IngestFileUploadView(APIView):
    """Ingest document from file upload"""
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Ingest document from file upload"""
        try:
            file = request.FILES.get('file')
            sector = request.data.get('sector', 'IT')
            
            if not file:
                return Response(
                    {"detail": "File is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a mock UploadFile-like object
            class MockUploadFile:
                def __init__(self, django_file):
                    self.filename = django_file.name
                    self.file = django_file
                    self._content = None
                
                async def read(self):
                    if self._content is None:
                        self._content = self.file.read()
                    return self._content
            
            mock_file = MockUploadFile(file)
            
            result = async_to_sync(ingest.ingest_file_upload)(
                file=mock_file,
                sector=sector
            )
            
            if hasattr(result, 'model_dump'):
                return Response(result.model_dump())
            elif hasattr(result, 'dict'):
                return Response(result.dict())
            else:
                return Response(result)
                
        except Exception as e:
            log.error(f"Ingest file upload error: {e}")
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
