from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from db.session import get_db  # 替换为你项目实际 Session 获取方式
from services.cases.case_service import create_case, get_case, list_cases, update_case, delete_case
from services.cases.case_service import create_task_for_case

from schemas.cases import CaseCreateRequest, CaseUpdateRequest, CaseResponse

router = APIRouter(prefix="/cases", tags=["Case Workflow"])

# ✅ 创建新案例
@router.post("/", response_model=CaseResponse)
def create_new_case(case_data: CaseCreateRequest, db: Session = Depends(get_db), user_id: int = 1):
    try:
        # user_id 这里简单用 1，实际可用 Depends(get_current_user) 获取
        case = create_case(
            db=db,
            user_id=user_id,
            case_name=case_data.case_name,
            description=case_data.description,
            target=case_data.target,
            constraints=case_data.constraints,
            dataset_id=case_data.dataset_id,
            model_id=case_data.model_id
        )
        return {"status": "success", "data": case}
    except Exception as e:
        print("Create Case error:", e)
        raise HTTPException(status_code=500, detail=str(e))

# 改 get_case_list
from typing import Dict

@router.get("/", response_model=Dict)
def get_case_list(db: Session = Depends(get_db), user_id: int = 1):
    try:
        cases = list_cases(db=db, user_id=user_id)
        return {"status": "success", "data": cases}  # ✅ 返回字典
    except Exception as e:
        print("List Cases error:", e)
        raise HTTPException(status_code=500, detail=str(e))

# ✅ 获取单个案例
@router.get("/{case_id}", response_model=CaseResponse)
def get_case_detail(case_id: int, db: Session = Depends(get_db)):
    try:
        case = get_case(db=db, case_id=case_id)
        return {"status": "success", "data": case}
    except Exception as e:
        print("Get Case error:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ✅ 更新案例
@router.put("/{case_id}", response_model=CaseResponse)
def update_case_info(case_id: int, case_data: CaseUpdateRequest, db: Session = Depends(get_db)):
    try:
        case = update_case(db=db, case_id=case_id, **case_data.dict(exclude_unset=True))
        return {"status": "success", "data": case}
    except Exception as e:
        print("Update Case error:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ✅ 删除案例
@router.delete("/{case_id}")
def delete_case_by_id(case_id: int, db: Session = Depends(get_db)):
    try:
        delete_case(db=db, case_id=case_id)
        return {"status": "success", "message": f"Case {case_id} deleted"}
    except Exception as e:
        print("Delete Case error:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ✅ 创建 Task 并绑定到 Case（可选接口）
@router.post("/{case_id}/tasks")
def create_task(case_id: int, step_name: str, db: Session = Depends(get_db)):
    try:
        task = create_task_for_case(db=db, case_id=case_id, step_name=step_name)
        return {"status": "success", "data": task}
    except Exception as e:
        print("Create Task for Case error:", e)
        raise HTTPException(status_code=500, detail=str(e))