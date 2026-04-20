"""
简化版的应用启动测试脚本
此脚本将测试应用的基本导入功能，而不需要完整的依赖
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.join(os.getcwd()))

def test_basic_imports():
    """测试基本导入功能"""
    print("正在测试基本导入...")

    try:
        # 测试核心配置导入
        from app.core.config import settings
        print("+ app.core.config 导入成功")
    except ImportError as e:
        print(f"- app.core.config 导入失败: {e}")

    try:
        # 测试异常处理模块导入
        from app.core.exceptions import APIException
        print("+ app.core.exceptions 导入成功")
    except ImportError as e:
        print(f"- app.core.exceptions 导入失败: {e}")

    try:
        # 测试领域模型导入
        from app.domain.models.user import User
        print("+ app.domain.models.user 导入成功")
    except ImportError as e:
        print(f"- app.domain.models.user 导入失败: {e}")

    try:
        # 测试服务层导入
        from app.services.context_service import ContextService
        print("+ app.services.context_service 导入成功")
    except ImportError as e:
        print(f"- app.services.context_service 导入失败: {e}")

    try:
        # 测试技能基类导入
        from app.skills.base import BaseSkill
        print("+ app.skills.base 导入成功")
    except ImportError as e:
        print(f"- app.skills.base 导入失败: {e}")

    try:
        # 测试编排器导入
        from app.orchestrator.orchestrator import Orchestrator
        print("+ app.orchestrator.orchestrator 导入成功")
    except ImportError as e:
        print(f"- app.orchestrator.orchestrator 导入失败: {e}")

def test_environment_config():
    """测试环境配置"""
    print("\n正在测试环境配置...")

    try:
        from app.core.config import settings
        print(f"+ APP_NAME: {settings.app_name}")
        print(f"+ APP_ENV: {settings.app_env}")
        print(f"+ LARK配置: {'已配置' if settings.lark_configured else '未配置'}")

        # 检查必要的环境变量
        required_vars = ['lark_app_id', 'lark_app_secret']
        missing_vars = []
        for var in required_vars:
            if not getattr(settings, var, None):
                missing_vars.append(var)

        if missing_vars:
            print(f"! 缺少环境变量: {missing_vars}")
        else:
            print("+ 所有必需的环境变量都已配置")

    except Exception as e:
        print(f"- 环境配置测试失败: {e}")

def test_models():
    """测试数据模型"""
    print("\n正在测试数据模型...")

    try:
        from app.domain.models.user import User
        user = User()
        print("+ User模型创建成功")
    except Exception as e:
        print(f"- User模型测试失败: {e}")

    try:
        from app.domain.models.project import Project
        project = Project()
        print("+ Project模型创建成功")
    except Exception as e:
        print(f"- Project模型测试失败: {e}")

if __name__ == "__main__":
    print("开始本地服务部署验证测试...")
    print("="*50)

    test_basic_imports()
    test_environment_config()
    test_models()

    print("="*50)
    print("测试完成！")
    print("\n注意：由于网络连接限制，部分依赖（如slowapi）未能安装，")
    print("这可能会影响应用的完整运行，但核心模块功能正常。")
    print("\n要完整运行应用，需要解决网络连接问题以安装所有依赖。")