from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_resource, models_flow
from pydantic import BaseModel
from typing import List, Dict
import pandas as pd
import io

router = APIRouter(prefix="/integration", tags=["Integration"])

class SurveyUpdate(BaseModel):
    block_id: str
    mined_tonnes: float
    remaining_tonnes: float
    status: str # Available, Mined, PartiallyMined

@router.post("/survey/actuals")
def import_survey_actuals(updates: List[SurveyUpdate], db: Session = Depends(get_db)):
    """
    Updates Block Model status based on Survey data.
    """
    updated_count = 0
    not_found = []
    
    for up in updates:
        # Find the block (ActivityArea)
        # Assuming block_id maps to area_id or name
        # Try both for robustness
        area = db.query(models_resource.ActivityArea).filter(models_resource.ActivityArea.area_id == up.block_id).first()
        if not area:
             area = db.query(models_resource.ActivityArea).filter(models_resource.ActivityArea.name == up.block_id).first()
             
        if area:
            # Update State
            if not area.slice_states:
                # Init if empty (shouldn't happen in configured system)
                area.slice_states = [{}]
                
            # Update the first slice ( Simplified for MVP)
            # In real system, we might split slices
            state = list(area.slice_states) # Copy
            current_slice = state[0]
            
            current_slice['quantity'] = up.remaining_tonnes
            current_slice['status'] = up.status
            
            area.slice_states = state # Reassign to trigger JSON update
            updated_count += 1
        else:
            not_found.append(up.block_id)
            
    db.commit()
    
    return {
        "message": f"Processed {len(updates)} updates.",
        "updated": updated_count,
        "not_found": not_found
    }

@router.post("/lab/quality")
def import_lab_results(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import Lab csv: StockpileID, CV, Ash, etc.
    """
    try:
        content = file.file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        results = []
        for index, row in df.iterrows():
            node_name = row.get('Stockpile')
            if not node_name: continue
            
            # Find Stockpile
            node = db.query(models_flow.FlowNode).filter(models_flow.FlowNode.name == node_name).first()
            if node and node.stockpile_config:
                # Update Quality Forcefully (Lab Override)
                config = node.stockpile_config
                current_q = config.current_grade_vector or {}
                
                # Update with columns found in CSV
                for col in df.columns:
                    if col in ['Stockpile', 'Date', 'SampleID']: continue
                    # Assume column match QualityField name
                    current_q[col] = float(row[col])
                    
                config.current_grade_vector = current_q
                results.append(node_name)
                
        db.commit()
        return {"message": "Lab Data Imported", "updated_stockpiles": results}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
