from django.db import models
from django.utils import timezone
import uuid

class Query(models.Model):
    """Stores user research queries"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query_text = models.TextField(help_text="The original user query")
    sector = models.CharField(
        max_length=50,
        choices=[
            ("IT", "IT"),
            ("Pharma", "Pharma"),
            ("Unknown", "Unknown"),
        ],
        default="Unknown",
        help_text="Sector assigned by query router"
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score from classification (0-1)"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("planning", "Planning"),
            ("researching", "Researching"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending"
    )
    plan_type = models.CharField(
        max_length=20,
        choices=[
            ("quick", "Quick"),
            ("standard", "Standard"),
            ("deep", "Deep"),
        ],
        null=True,
        blank=True,
        help_text="Selected research plan type"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Queries"
    
    def __str__(self):
        return f"{self.query_text[:50]}... ({self.sector})"

class ResearchStep(models.Model):
    """Tracks individual research steps during deep research"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.ForeignKey(
        Query,
        on_delete=models.CASCADE,
        related_name="research_steps"
    )
    step_number = models.IntegerField(help_text="Sequential step number")
    action = models.CharField(
        max_length=200,
        help_text="Action being performed (e.g., 'Searching for...')"
    )
    source = models.CharField(
        max_length=100,
        choices=[
            ("Tavily", "Tavily"),
            ("yfinance", "yfinance"),
            ("Web", "Web"),
            ("RAG", "RAG"),
            ("API", "API"),
        ],
        help_text="Data source used"
    )
    query_text = models.TextField(
        help_text="The specific query/search term used"
    )
    finding = models.TextField(
        null=True,
        blank=True,
        help_text="Key finding from this step"
    )
    raw_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw response data from source"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ["query", "step_number"]
        unique_together = [["query", "step_number"]]
    
    def __str__(self):
        return f"Step {self.step_number}: {self.action}"

class Report(models.Model):
    """Stores generated research reports"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.OneToOneField(
        Query,
        on_delete=models.CASCADE,
        related_name="report"
    )
    title = models.CharField(max_length=200, help_text="Report title")
    content = models.TextField(help_text="Full report content in markdown")
    executive_summary = models.TextField(
        null=True,
        blank=True,
        help_text="Executive summary extracted from report"
    )
    total_steps = models.IntegerField(
        default=0,
        help_text="Total research steps completed"
    )
    duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Total research duration"
    )
    citations = models.JSONField(
        default=list,
        help_text="List of citations with URLs"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata (dimensions covered, etc.)"
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Report: {self.title}"