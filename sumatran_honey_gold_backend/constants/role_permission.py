from ..constants.role import Role as RoleConstant

class RolePermission:
    @staticmethod
    def is_mentor(user) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        role = getattr(user, "role", None)
        return bool(role and role.id_role == RoleConstant.MENTOR.value)

    @staticmethod
    def is_teacher(user) -> bool:
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, "role", None)
        return bool(role and role.id_role == RoleConstant.TEACHER.value)