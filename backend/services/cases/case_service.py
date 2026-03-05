import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.db_models.case_table import Case  # 注意路径，替换为你实际路径
from db.db_models.task_table import TaskTable  # 如果需要绑定 Task

# ✅ 创建新 Case
def create_case(
    db: Session,
    user_id: int,
    case_name: str,
    description: str | None = None,
    target: str | None = None,
    constraints: str | None = None,
    dataset_id: int | None = None,
    model_id: int | None = None
) -> Case:
    case = Case(
        case_name=case_name,
        description=description,
        target=target,
        constraints=constraints,
        user_id=user_id,
        dataset_id=dataset_id,
        model_id=model_id,
        current_step=1,
        status="initialized",
        created_at=datetime.datetime.utcnow()
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case

# ✅ 获取单个 Case
def get_case(db: Session, case_id: int) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case

# ✅ 获取用户所有 Case
def list_cases(db: Session, user_id: int) -> list[Case]:
    return db.query(Case).filter(Case.user_id == user_id).order_by(Case.created_at.desc()).all()

# ✅ 更新 Case
def update_case(
    db: Session,
    case_id: int,
    **kwargs
) -> Case:
    case = get_case(db, case_id)
    allowed_fields = ["case_name", "description", "target", "constraints", "dataset_id", "model_id", "current_step", "status"]
    for key, value in kwargs.items():
        if key in allowed_fields:
            setattr(case, key, value)
    db.commit()
    db.refresh(case)
    return case

# ✅ 删除 Case
def delete_case(db: Session, case_id: int):
    case = get_case(db, case_id)
    # 可选：删除该 Case 绑定的任务
    tasks = db.query(TaskTable).filter(TaskTable.case_id == case.id).all()
    for t in tasks:
        db.delete(t)
    db.delete(case)
    db.commit()

# ✅ 生成 Task 并绑定 Case（可选）
def create_task_for_case(
    db: Session,
    case_id: int,
    step_name: str,
    parameters: dict | None = None
) -> TaskTable:
    from db.db_models.task_table import TaskTable  # 防止循环导入
    case = get_case(db, case_id)
    task = TaskTable(
        case_id=case.id,
        step_name=step_name,
        status="initialized",
        parameters=parameters
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 更新 Case current_step 或状态
    # 这里可以根据 step_name 定义顺序更新 current_step
    # 简单示例：
    case.current_step += 1
    case.status = "running"
    db.commit()
    db.refresh(case)
    return task