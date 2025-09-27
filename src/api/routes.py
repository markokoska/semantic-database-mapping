

import asyncio
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import tempfile
import os
from pathlib import Path

from ..core.models import SchemaMapping, MappingJob
from ..core.mapping_engine import MappingEngine
from ..semantic.rdf_generator import RDFGenerator

logger = logging.getLogger(__name__)

mapping_engine = MappingEngine()
rdf_generator = RDFGenerator()

router = APIRouter(tags=["semantic-mapping"])


@router.post("/upload-schema", response_model=Dict[str, str])
async def upload_schema_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> Dict[str, str]:

    try:
        allowed_extensions = ['.csv', '.json', '.sqlite', '.db']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {allowed_extensions}"
            )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        job_id = await mapping_engine.create_mapping_job(temp_file_path)
        
        background_tasks.add_task(process_mapping_job_background, job_id, temp_file_path)
        
        return {"job_id": job_id, "status": "created", "message": "File uploaded successfully"}
        
    except Exception as e:
        logger.error(f"Error uploading schema file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_mapping_job_background(job_id: str, temp_file_path: str):
    try:
        await mapping_engine.process_mapping_job(job_id)
        logger.info(f"Completed background processing for job {job_id}")
    except Exception as e:
        logger.error(f"Error in background processing for job {job_id}: {e}")
    finally:
        try:
            os.unlink(temp_file_path)
        except:
            pass


@router.get("/job/{job_id}", response_model=MappingJob)
async def get_job_status(job_id: str) -> MappingJob:
    try:
        job = mapping_engine.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/mapping", response_model=SchemaMapping)
async def get_schema_mapping(job_id: str) -> SchemaMapping:
    try:
        job = mapping_engine.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        if not job.result:
            raise HTTPException(status_code=500, detail="Job completed but no results available")
        
        return job.result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schema mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/rdf")
async def export_rdf_ontology(job_id: str, format: str = "turtle"):
    try:
        job = mapping_engine.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "completed" or not job.result:
            raise HTTPException(status_code=400, detail="Job not completed or no results")
        
        rdf_graph = rdf_generator.generate_ontology(job.result)
        
        file_extensions = {
            "turtle": ".ttl",
            "xml": ".rdf",
            "n3": ".n3",
            "json-ld": ".jsonld"
        }
        
        if format not in file_extensions:
            raise HTTPException(status_code=400, detail="Unsupported RDF format")
        
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=file_extensions[format]
        ) as temp_file:
            rdf_graph.serialize(destination=temp_file.name, format=format)
            
            return FileResponse(
                temp_file.name,
                media_type="application/octet-stream",
                filename=f"ontology_{job_id}{file_extensions[format]}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting RDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[str])
async def list_active_jobs() -> List[str]:
    try:
        return mapping_engine.list_active_jobs()
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/job/{job_id}")
async def delete_job(job_id: str) -> Dict[str, str]:
    try:
        if job_id not in mapping_engine.active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        del mapping_engine.active_jobs[job_id]
        
        return {"message": f"Job {job_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_jobs(max_age_hours: int = 24) -> Dict[str, str]:

    try:
        initial_count = len(mapping_engine.active_jobs)
        mapping_engine.cleanup_completed_jobs(max_age_hours)
        final_count = len(mapping_engine.active_jobs)
        
        cleaned_count = initial_count - final_count
        
        return {
            "message": f"Cleaned up {cleaned_count} old jobs",
            "remaining_jobs": final_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "service": "Semantic Database Schema Mapping System",
        "active_jobs": str(len(mapping_engine.active_jobs))
    }
