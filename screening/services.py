"""
Screening Services Module
Integrates the ML pipeline with Django models and views.
"""

import logging
from typing import List, Optional
from django.conf import settings
from django.utils import timezone

from ml.pipeline import ScreeningPipeline, quick_screen
from ml.job_analyzer import JobRequirements

logger = logging.getLogger(__name__)


class ScreeningService:
    """
    Service layer for AI-powered resume screening.

    Handles the integration between Django models and the ML pipeline.
    """

    def __init__(self):
        self.pipeline = ScreeningPipeline()

    def screen_candidate_for_job(self, candidate, job) -> dict:
        """
        Screen a single candidate for a specific job.

        Args:
            candidate: Candidate model instance
            job: Job model instance

        Returns:
            Dictionary with screening results
        """
        # Get the candidate's latest resume
        resume = candidate.resumes.filter(status='completed').order_by('-processed_at').first()
        if not resume:
            # Try to get any resume
            resume = candidate.resumes.order_by('-uploaded_at').first()

        if not resume or not resume.extracted_text:
            logger.warning(f"No extracted text for candidate {candidate.id}")
            return {
                'success': False,
                'error': 'No resume text available for screening'
            }

        # Prepare job description from job model
        job_description = self._build_job_description(job)

        # Run quick screen
        try:
            result = quick_screen(resume.extracted_text, job_description)
            result['success'] = True
            return result
        except Exception as e:
            logger.error(f"Error screening candidate {candidate.id} for job {job.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def screen_resume_for_job(self, resume, job) -> dict:
        """
        Screen a specific resume for a job.

        Args:
            resume: Resume model instance
            job: Job model instance

        Returns:
            Dictionary with screening results
        """
        if not resume.extracted_text:
            return {
                'success': False,
                'error': 'Resume text not extracted yet'
            }

        job_description = self._build_job_description(job)

        try:
            result = quick_screen(resume.extracted_text, job_description)
            result['success'] = True
            return result
        except Exception as e:
            logger.error(f"Error screening resume {resume.id} for job {job.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def screen_all_candidates_for_job(self, job, candidates=None) -> List[dict]:
        """
        Screen all candidates for a specific job.

        Args:
            job: Job model instance
            candidates: Optional queryset of candidates (defaults to all with completed resumes)

        Returns:
            List of screening results sorted by score
        """
        if candidates is None:
            from resumes.models import Candidate
            candidates = Candidate.objects.filter(
                resumes__status='completed'
            ).distinct()

        job_description = self._build_job_description(job)
        results = []

        for candidate in candidates:
            resume = candidate.resumes.filter(status='completed').order_by('-processed_at').first()
            if resume and resume.extracted_text:
                result = quick_screen(resume.extracted_text, job_description)
                result['candidate_id'] = candidate.id
                result['candidate_name'] = candidate.name
                result['candidate_email'] = candidate.email
                result['resume_id'] = resume.id
                results.append(result)

        # Sort by overall score descending
        results.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
        return results

    def create_screening_result(self, candidate, job, screening_data: dict) -> 'ScreeningResult':
        """
        Create or update a ScreeningResult model from screening data.

        Args:
            candidate: Candidate model instance
            job: Job model instance
            screening_data: Dictionary from quick_screen()

        Returns:
            ScreeningResult model instance
        """
        from screening.models import ScreeningResult

        # Extract data
        overall_score = screening_data.get('overall_score', 0)
        skill_score = screening_data.get('skill_score', 0)
        semantic_score = screening_data.get('semantic_score', 0)
        experience_score = screening_data.get('experience_score', 0)
        education_score = screening_data.get('education_score', 0)
        preferred_skill_score = screening_data.get('preferred_skill_score', 0)

        matched_skills = screening_data.get('matched_skills', [])
        missing_skills = screening_data.get('missing_skills', [])
        missing_preferred_skills = screening_data.get('missing_preferred_skills', [])

        recommendation = screening_data.get('recommendation', 'Not Recommended')
        confidence = screening_data.get('confidence', 0)
        rationale = screening_data.get('rationale', '')
        strengths = screening_data.get('strengths', [])
        weaknesses = screening_data.get('concerns', [])

        # Create or update
        result, created = ScreeningResult.objects.update_or_create(
            candidate=candidate,
            job=job,
            defaults={
                'overall_score': overall_score,
                'skill_score': skill_score,
                'semantic_score': semantic_score,
                'experience_score': experience_score,
                'education_score': education_score,
                'preferred_skill_score': preferred_skill_score,
                'matched_skills': matched_skills,
                'missing_skills': missing_skills,
                'missing_preferred_skills': missing_preferred_skills,
                'explanation': rationale,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'recommendation': recommendation,
                'status': 'screened',
                'screened_at': timezone.now(),
            }
        )

        return result

    def batch_screen_job(self, job, created_by=None) -> 'ScreeningBatch':
        """
        Create and run a batch screening job for all candidates.

        Args:
            job: Job model instance
            created_by: User who initiated the batch

        Returns:
            ScreeningBatch model instance
        """
        from screening.models import ScreeningBatch

        # Create batch record
        candidates = self._get_candidates_with_resumes()
        batch = ScreeningBatch.objects.create(
            job=job,
            name=f"Batch screening for {job.title} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            total_resumes=len(candidates),
            created_by=created_by,
            status='processing'
        )

        job_description = self._build_job_description(job)

        processed = 0
        for candidate in candidates:
            resume = candidate.resumes.filter(status='completed').order_by('-processed_at').first()
            if resume and resume.extracted_text:
                screening_data = quick_screen(resume.extracted_text, job_description)
                self.create_screening_result(candidate, job, screening_data)
                processed += 1

        # Update batch
        batch.processed_resumes = processed
        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()

        return batch

    def _build_job_description(self, job) -> str:
        """Build a comprehensive job description text from Job model."""
        parts = [
            f"Job Title: {job.title}",
            f"Company: {job.company.username}",
            f"Description: {job.description}",
        ]

        if job.required_skills:
            parts.append(f"Required Skills: {job.required_skills}")

        if job.preferred_skills:
            parts.append(f"Preferred Skills: {job.preferred_skills}")

        if job.minimum_experience:
            parts.append(f"Experience Required: {job.minimum_experience} years")

        if job.education_requirement:
            parts.append(f"Education Required: {job.education_requirement}")

        if job.location:
            parts.append(f"Location: {job.location}")

        if job.employment_type:
            parts.append(f"Employment Type: {job.get_employment_type_display()}")

        return '\n\n'.join(parts)

    def _get_candidates_with_resumes(self):
        """Get all candidates who have completed resumes."""
        from resumes.models import Candidate
        return Candidate.objects.filter(
            resumes__status='completed'
        ).distinct()

    def extract_resume_text(self, resume) -> bool:
        """
        Extract text from a resume file and update the resume model.

        Args:
            resume: Resume model instance

        Returns:
            True if successful, False otherwise
        """
        try:
            resume.status = 'processing'
            resume.save()

            # Extract text using ML pipeline
            text, metadata = self.pipeline.resume_parser.extract_text(resume.file.path)

            # Update resume
            resume.extracted_text = text
            resume.status = 'completed'
            resume.processed_at = timezone.now()
            resume.save()

            # Also update candidate with extracted info
            self._update_candidate_from_resume(resume.candidate, text)

            return True

        except Exception as e:
            logger.error(f"Error extracting text from resume {resume.id}: {e}")
            resume.status = 'failed'
            resume.error_message = str(e)
            resume.save()
            return False

    def _update_candidate_from_resume(self, candidate, resume_text: str):
        """Update candidate profile from extracted resume text."""
        # Extract skills
        skills_result = self.pipeline.skill_extractor.extract_skills(resume_text)
        skills = skills_result.get('skills', [])

        # Extract experience
        experience = self.pipeline.skill_extractor.extract_experience_years(resume_text)

        # Extract education
        education_list = self.pipeline.skill_extractor.extract_education(resume_text)
        education_text = '; '.join(education_list) if education_list else ''

        # Extract certifications
        certs = self.pipeline.skill_extractor.extract_certifications(resume_text)

        # Update candidate
        candidate.skills = skills
        candidate.total_experience = experience
        candidate.education = education_text
        candidate.certifications = certs
        candidate.save()


# Singleton instance
_screening_service = None


def get_screening_service() -> ScreeningService:
    """Get the singleton ScreeningService instance."""
    global _screening_service
    if _screening_service is None:
        _screening_service = ScreeningService()
    return _screening_service