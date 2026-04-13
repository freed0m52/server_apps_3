from fastapi import HTTPException, Depends, status
from typing import List
from auth import get_current_user, fake_users_db, user_roles

class Role:
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

ROLE_PERMISSIONS = {
    Role.ADMIN: ["create", "read", "update", "delete"],
    Role.USER: ["read", "update"],
    Role.GUEST: ["read"],
}

def require_role(required_roles: List[str]):
    async def role_checker(current_user: str = Depends(get_current_user)):
        user_role = user_roles.get(current_user, Role.GUEST)
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {required_roles}, your role: {user_role}"
            )
        return current_user
    return role_checker

def has_permission(username: str, permission: str) -> bool:
    user_role = user_roles.get(username, Role.GUEST)
    return permission in ROLE_PERMISSIONS.get(user_role, [])