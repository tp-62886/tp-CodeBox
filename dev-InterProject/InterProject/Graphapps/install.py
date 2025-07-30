#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Graphapps知识图谱功能安装脚本
自动检查和安装所需依赖
"""

import os
import sys
import subprocess
import importlib
import platform

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本检查通过: {sys.version}")
    return True

def check_package(package_name, import_name=None):
    """检查包是否已安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} 已安装")
        return True
    except ImportError:
        print(f"❌ {package_name} 未安装")
        return False

def install_package(package_name):
    """安装包"""
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package_name} 安装失败")
        return False

def install_requirements(requirements_file="requirements-minimal.txt"):
    """从requirements文件安装依赖"""
    if not os.path.exists(requirements_file):
        print(f"❌ 找不到requirements文件: {requirements_file}")
        return False
    
    try:
        print(f"正在从 {requirements_file} 安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("✅ 所有依赖安装成功")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依赖安装失败")
        return False

def check_neo4j_connection():
    """检查Neo4j连接"""
    try:
        from neo4j import GraphDatabase
        
        # 尝试连接Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("✅ Neo4j连接成功")
                driver.close()
                return True
        driver.close()
    except Exception as e:
        print(f"❌ Neo4j连接失败: {str(e)}")
        print("请确保Neo4j数据库已启动，并检查连接配置")
        return False

def create_env_file():
    """创建环境变量文件"""
    env_content = """# Graphapps环境变量配置
# Neo4j数据库配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12345678

# Django配置
DEBUG=True
SECRET_KEY=your-secret-key-here

# 其他配置
PYTHONPATH=.
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("✅ 创建了 .env 环境变量文件")
        print("请根据实际情况修改 .env 文件中的配置")
    else:
        print("✅ .env 文件已存在")

def main():
    """主安装流程"""
    print("=" * 50)
    print("Graphapps知识图谱功能安装脚本")
    print("=" * 50)
    
    # 1. 检查Python版本
    if not check_python_version():
        return False
    
    # 2. 升级pip
    print("\n正在升级pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ pip升级成功")
    except:
        print("⚠️ pip升级失败，继续安装...")
    
    # 3. 选择安装模式
    print("\n请选择安装模式:")
    print("1. 最小安装（仅核心功能）")
    print("2. 完整安装（包含所有功能）")
    
    choice = input("请输入选择 (1/2，默认为1): ").strip()
    
    if choice == "2":
        requirements_file = "requirements.txt"
        print("选择完整安装模式")
    else:
        requirements_file = "requirements-minimal.txt"
        print("选择最小安装模式")
    
    # 4. 安装依赖
    print(f"\n开始安装依赖...")
    if not install_requirements(requirements_file):
        return False
    
    # 5. 检查关键包
    print("\n检查关键包安装状态...")
    critical_packages = [
        ("Django", "django"),
        ("Neo4j Driver", "neo4j"),
        ("Pandas", "pandas"),
        ("NumPy", "numpy"),
        ("Jieba", "jieba"),
        ("Requests", "requests")
    ]
    
    all_installed = True
    for package_name, import_name in critical_packages:
        if not check_package(package_name, import_name):
            all_installed = False
    
    if not all_installed:
        print("❌ 部分关键包安装失败，请手动安装")
        return False
    
    # 6. 创建环境变量文件
    print("\n创建环境配置...")
    create_env_file()
    
    # 7. 检查Neo4j连接（可选）
    print("\n检查Neo4j连接...")
    neo4j_ok = check_neo4j_connection()
    
    # 8. 安装总结
    print("\n" + "=" * 50)
    print("安装完成总结:")
    print("=" * 50)
    print("✅ Python环境检查通过")
    print("✅ 依赖包安装完成")
    print("✅ 环境配置文件已创建")
    
    if neo4j_ok:
        print("✅ Neo4j连接正常")
    else:
        print("⚠️ Neo4j连接失败，请检查数据库配置")
    
    print("\n下一步操作:")
    print("1. 如果Neo4j连接失败，请启动Neo4j数据库")
    print("2. 根据需要修改 .env 文件中的配置")
    print("3. 运行 python manage.py runserver 启动Django服务")
    print("4. 访问 http://127.0.0.1:8000/Graphapps/ 查看知识图谱")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 安装成功！")
        sys.exit(0)
    else:
        print("\n💥 安装失败，请检查错误信息")
        sys.exit(1)
