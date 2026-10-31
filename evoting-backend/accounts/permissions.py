from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        u = request.user

        return bool(
            u
            and u.is_authenticated
            and u.role in self.allowed_roles
        )


def roles(*names):
    """
    Usage:
    permission_classes = [roles("election_admin")]
    """

    return type(
        "RolePerm_" + "_".join(names),
        (RolePermission,),
        {"allowed_roles": names}
    )