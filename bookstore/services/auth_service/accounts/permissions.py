"""
Permission Matrix — định nghĩa tập trung toàn bộ quyền của hệ thống.
Chạy lệnh: python manage.py seed_permissions để tạo dữ liệu vào DB.

Format codename: {service}:{resource}:{action}
"""

PERMISSION_MATRIX = {

    # ══════════════════════════════════════════════════════
    # AUTH SERVICE
    # ══════════════════════════════════════════════════════
    'auth': {
        'user': {
            'read_own':    'Xem thông tin cá nhân',
            'update_own':  'Cập nhật thông tin cá nhân',
            'delete_own':  'Xoá tài khoản',
            'read_all':    'Xem tất cả users (admin)',
            'update_all':  'Cập nhật bất kỳ user (admin)',
            'ban':         'Ban user (admin)',
        },
        'role': {
            'assign':  'Gán role cho user (admin)',
            'revoke':  'Thu hồi role (admin)',
        },
        'seller_profile': {
            'create':      'Tạo hồ sơ người bán',
            'read_own':    'Xem hồ sơ người bán của mình',
            'update_own':  'Cập nhật hồ sơ người bán',
            'verify':      'Duyệt hồ sơ người bán (admin)',
        },
        'author_profile': {
            'create':      'Tạo hồ sơ tác giả',
            'read_own':    'Xem hồ sơ tác giả của mình',
            'update_own':  'Cập nhật hồ sơ tác giả',
            'verify':      'Xác minh tác giả (admin)',
        },
    },

    # ══════════════════════════════════════════════════════
    # CATALOG SERVICE
    # ══════════════════════════════════════════════════════
    'catalog': {
        'book': {
            'read':        'Xem sách (public)',
            'create':      'Đăng sách lên (seller)',
            'update_own':  'Sửa sách của shop mình (seller)',
            'delete_own':  'Xoá sách của shop mình (seller)',
            'update_all':  'Sửa bất kỳ sách (admin)',
            'delete_all':  'Xoá bất kỳ sách (admin)',
            'publish':     'Duyệt & publish sách (admin)',
            'manage_price':'Quản lý giá & khuyến mãi (seller)',
            'manage_stock':'Quản lý tồn kho (seller)',
        },
        'author': {
            'read':        'Xem danh sách tác giả (public)',
            'create':      'Tạo tác giả (admin + seller)',
            'update_own':  'Sửa profile tác giả của mình (author)',
            'update_all':  'Sửa bất kỳ tác giả (admin)',
            'delete':      'Xoá tác giả (admin)',
            'link_book':   'Gắn tác giả vào sách (seller)',
        },
        'category': {
            'read':    'Xem danh mục (public)',
            'manage':  'CRUD danh mục (admin)',
        },
        'publisher': {
            'read':    'Xem nhà xuất bản (public)',
            'manage':  'CRUD nhà xuất bản (admin + seller)',
        },
    },

    # ══════════════════════════════════════════════════════
    # SHOP SERVICE
    # ══════════════════════════════════════════════════════
    'shop': {
        'shop': {
            'read':        'Xem danh sách shop (public)',
            'create':      'Tạo shop (seller đã verified)',
            'update_own':  'Sửa shop của mình (seller)',
            'delete_own':  'Đóng shop của mình (seller)',
            'update_all':  'Sửa bất kỳ shop (admin)',
            'suspend':     'Tạm đình chỉ shop (admin)',
            'verify':      'Xác minh shop (admin)',
            'follow':      'Follow shop (customer)',
        },
        'shop_staff': {
            'manage':      'Quản lý nhân viên shop (seller/manager)',
        },
    },

    # ══════════════════════════════════════════════════════
    # ORDER SERVICE
    # ══════════════════════════════════════════════════════
    'order': {
        'cart': {
            'manage':    'Quản lý giỏ hàng của mình',
        },
        'order': {
            'create':      'Đặt hàng',
            'read_own':    'Xem đơn hàng của mình',
            'cancel_own':  'Huỷ đơn hàng của mình',
            'read_shop':   'Xem đơn hàng của shop mình (seller)',
            'update_shop': 'Cập nhật trạng thái đơn (seller)',
            'read_all':    'Xem tất cả đơn hàng (admin)',
            'update_all':  'Cập nhật bất kỳ đơn (admin)',
        },
        'address': {
            'manage':    'Quản lý địa chỉ giao hàng',
        },
        'payment': {
            'read_own':  'Xem thanh toán của mình',
            'refund':    'Hoàn tiền (admin)',
            'read_all':  'Xem tất cả thanh toán (admin)',
        },
    },

    # ══════════════════════════════════════════════════════
    # INTERACTION SERVICE
    # ══════════════════════════════════════════════════════
    'interaction': {
        'review': {
            'read':       'Xem đánh giá (public)',
            'create':     'Viết đánh giá (customer đã mua)',
            'update_own': 'Sửa đánh giá của mình',
            'delete_own': 'Xoá đánh giá của mình',
            'delete_all': 'Xoá bất kỳ đánh giá (admin)',
            'reply':      'Phản hồi đánh giá (seller)',
            'moderate':   'Ẩn/duyệt đánh giá (admin)',
        },
        'wishlist': {
            'manage':    'Quản lý wishlist',
        },
        'coupon': {
            'read_own':   'Xem coupon đang có',
            'use':        'Dùng coupon khi checkout',
            'manage':     'CRUD coupon (admin + seller)',
        },
    },
}


# ── Role → Permission mapping ──────────────────────────────────────────────────
# Key: role name
# Value: list of codenames (service:resource:action)

ROLE_PERMISSIONS = {

    'customer': [
        # Auth
        'auth:user:read_own',
        'auth:user:update_own',
        'auth:user:delete_own',
        # Catalog (read only)
        'catalog:book:read',
        'catalog:author:read',
        'catalog:category:read',
        'catalog:publisher:read',
        # Shop
        'shop:shop:read',
        'shop:shop:follow',
        # Order
        'order:cart:manage',
        'order:order:create',
        'order:order:read_own',
        'order:order:cancel_own',
        'order:address:manage',
        'order:payment:read_own',
        # Interaction
        'interaction:review:read',
        'interaction:review:create',
        'interaction:review:update_own',
        'interaction:review:delete_own',
        'interaction:wishlist:manage',
        'interaction:coupon:read_own',
        'interaction:coupon:use',
    ],

    'seller': [
        # Kế thừa tất cả quyền customer
        'auth:user:read_own',
        'auth:user:update_own',
        'auth:seller_profile:create',
        'auth:seller_profile:read_own',
        'auth:seller_profile:update_own',
        # Catalog
        'catalog:book:read',
        'catalog:book:create',
        'catalog:book:update_own',
        'catalog:book:delete_own',
        'catalog:book:manage_price',
        'catalog:book:manage_stock',
        'catalog:author:read',
        'catalog:author:create',
        'catalog:author:link_book',
        'catalog:category:read',
        'catalog:publisher:read',
        'catalog:publisher:manage',
        # Shop
        'shop:shop:read',
        'shop:shop:create',
        'shop:shop:update_own',
        'shop:shop:delete_own',
        'shop:shop_staff:manage',
        # Order
        'order:order:read_shop',
        'order:order:update_shop',
        # Interaction
        'interaction:review:read',
        'interaction:review:reply',
        'interaction:coupon:manage',
        'interaction:wishlist:manage',
    ],

    'author': [
        # Auth
        'auth:user:read_own',
        'auth:user:update_own',
        'auth:author_profile:create',
        'auth:author_profile:read_own',
        'auth:author_profile:update_own',
        # Catalog — chỉ sửa profile tác giả của mình
        'catalog:book:read',
        'catalog:author:read',
        'catalog:author:update_own',
        'catalog:category:read',
        'catalog:publisher:read',
        # Shop
        'shop:shop:read',
        # Order — xem doanh thu / royalty (read-only)
        'order:order:read_own',
        'order:payment:read_own',
        # Interaction
        'interaction:review:read',
        'interaction:wishlist:manage',
    ],

    'admin': [
        # Full access — mọi permission
        'auth:user:read_own',
        'auth:user:update_own',
        'auth:user:read_all',
        'auth:user:update_all',
        'auth:user:ban',
        'auth:role:assign',
        'auth:role:revoke',
        'auth:seller_profile:verify',
        'auth:author_profile:verify',
        # Catalog
        'catalog:book:read',
        'catalog:book:create',
        'catalog:book:update_all',
        'catalog:book:delete_all',
        'catalog:book:publish',
        'catalog:author:read',
        'catalog:author:create',
        'catalog:author:update_all',
        'catalog:author:delete',
        'catalog:category:read',
        'catalog:category:manage',
        'catalog:publisher:read',
        'catalog:publisher:manage',
        # Shop
        'shop:shop:read',
        'shop:shop:update_all',
        'shop:shop:suspend',
        'shop:shop:verify',
        # Order
        'order:order:read_all',
        'order:order:update_all',
        'order:payment:read_all',
        'order:payment:refund',
        # Interaction
        'interaction:review:read',
        'interaction:review:delete_all',
        'interaction:review:moderate',
        'interaction:coupon:manage',
    ],
}
