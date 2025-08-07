import os
import subprocess
import shutil
import json
import matplotlib.pyplot as plt

def add_region(
    target_case_path: str,  
    fire_num: int,        # 总点火区数
    index: int,              # 当前区域索引
    region: str,        # 当前区域类型
    yaml_path: str           # 配置文件路径
) -> dict:
    """
    添加区域到案例中，生成对应的JSON配置文件
    
    参数:
        target_case_path: 目标案例路径
        fire_num: 区域总数
        index: 当前区域索引
        region_type: 区域类型
        yaml_path: 配置文件路径
        
    返回:
        操作结果字典
    """
    try:
        # 1. 读取YAML/JSON配置文件
        with open(yaml_path, 'r') as file:
            config_data = json.load(file)  # 假设是JSON格式文件

        region_type = f'{region}_{fire_num}_{index}'
        
        # 2. 检查配置中是否存在对应区域类型的数据
        if region_type not in config_data:
            return {
                "status": "error",
                "error_message": f"区域类型 '{region_type}' 在配置文件中未找到"
            }
        
        # 3. 获取该区域类型的配置
        region_config = config_data[region_type]
        
        # 4. 创建目标文件名
        filename = f"{region_type}.json"
        target_file = os.path.join(target_case_path, filename)
        
        # 5. 将配置写入文件
        with open(target_file, 'w') as outfile:
            json.dump(region_config, outfile, indent=4)
        
        return {
            "status": "success",
            "message": f"成功生成区域配置文件: {filename}",
            "file_path": target_file
        }
        
    except FileNotFoundError:
        return {
            "status": "error",
            "error_message": f"配置文件未找到: {yaml_path}"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "error_message": f"配置文件格式错误: {yaml_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"添加区域失败: {str(e)}"
        }
    
def conduct_add_region(
    target_case_path: str,  
    fire_num: int,        # 总点火区数
    index: int,              # 当前区域索引
    region: str,        # 当前区域类型
) -> dict:
    # 1. 读取JSON配置文件（虽然文件名是.yaml，但实际是JSON格式）
    yaml_name = f'{region}_{fire_num}_{index}.json'
    yaml_path = os.path.join(target_case_path, yaml_name)
    
    with open(yaml_path, 'r') as f:
        config_data = json.load(f)

    if region == 'circle':
        # 提取参数（去除括号）
        p1 = config_data["p1"].strip("()")
        p2 = config_data["p2"].strip("()")
        radius = config_data["radius"]
        
        # 2. 构建要添加的cylinderToCell块
        new_block = f"""    cylinderToCell
        {{
            p1 ({p1});
            p2 ({p2});
            radius {radius};
            fieldValues
            (
                volScalarFieldValue T    2562.9164474426
                volScalarFieldValue H      0.0001388161
                volScalarFieldValue H2     0.0017201967
                volScalarFieldValue O      0.0007829835
                volScalarFieldValue OH     0.0088649505
                volScalarFieldValue H2O    0.2335677169
                volScalarFieldValue O2     0.0097972807
                volScalarFieldValue HO2    0.0000040007
                volScalarFieldValue H2O2   0.0000004494
                volScalarFieldValue N2     0.7451236055
            );
        }}"""


    elif region == 'square':

        p1 = config_data["p1"].strip("()")
        p2 = config_data["p2"].strip("()")
            
        new_block = f"""    boxToCell
        {{  
            boxes
            (
                ({p1})({p2})
            );
            fieldValues
            (
                volScalarFieldValue T    2562.9164474426
                volScalarFieldValue H      0.0001388161
                volScalarFieldValue H2     0.0017201967
                volScalarFieldValue O      0.0007829835
                volScalarFieldValue OH     0.0088649505
                volScalarFieldValue H2O    0.2335677169
                volScalarFieldValue O2     0.0097972807
                volScalarFieldValue HO2    0.0000040007
                volScalarFieldValue H2O2   0.0000004494
                volScalarFieldValue N2     0.7451236055
            );
        }}"""


    else:
        p1 = config_data["p1"].strip("()")
        p2 = config_data["p2"].strip("()")
        radius = config_data["radius"]
        radius2 = 2 * float(radius)
        
        # 2. 构建要添加的cylinderToCell块
        new_block = f"""    cylinderAnnulusToCell
        {{
            p1 ({p1});
            p2 ({p2});
            innerRadius {radius};
            outerRadius {radius2};
            fieldValues
            (
                volScalarFieldValue T    2562.9164474426
                volScalarFieldValue H      0.0001388161
                volScalarFieldValue H2     0.0017201967
                volScalarFieldValue O      0.0007829835
                volScalarFieldValue OH     0.0088649505
                volScalarFieldValue H2O    0.2335677169
                volScalarFieldValue O2     0.0097972807
                volScalarFieldValue HO2    0.0000040007
                volScalarFieldValue H2O2   0.0000004494
                volScalarFieldValue N2     0.7451236055
            );
        }}"""


    
    # 3. 读取并修改setFieldsDict文件
    set_fields_path = os.path.join(target_case_path, "system", "setFieldsDict")
    
    with open(set_fields_path, 'r') as f:
        lines = f.readlines()
    
    # 查找包含"regions"的行
    new_lines = []
    inserted = False
    for i, line in enumerate(lines):
        new_lines.append(line)
   
        if inserted:

            new_lines.append("\n")
            new_lines.append("\n")
                
            new_lines.append(new_block)
            inserted = False

        if "regions" in line:
            inserted = True
            
    
    # 4. 写回修改后的文件
    with open(set_fields_path, 'w') as f:
        f.writelines(new_lines)
    
    return {
        "status": "success",
        "inserted_block": new_block,
        "config_path": yaml_path,
        "set_fields_path": set_fields_path
    }



def copy_from_standard(
    standard_case_path: str,
    target_case_path: str,
    case_name: str,
    region_type: list,
    switch: bool
) -> dict:
    
    # 构建目标案例路径（按类型命名）
    target_case_dir = os.path.join(target_case_path, case_name)
    
    try:
        # 复制整个标准案例到目标路径
        shutil.copytree(standard_case_path, target_case_dir)
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to copy standard case: {str(e)}"
        }
    
    for i in range(len(region_type)):
        add_region(target_case_dir, len(region_type), i+1, region_type[i], '/home/xk/Software/6_bohr_agent/deepflame-agent-dev/df_agent/agent/files/HIT_Fields.json')
        conduct_add_region(target_case_dir, len(region_type), i+1, region_type[i])

    

    if switch == True:
        run_script = os.path.join(target_case_dir, 'sub.sh')
        if not os.path.isfile(run_script):
            return {
                "status": "error",
                "error_message": "sub.sh script not found in target directory"
            }
        try:
            result = subprocess.run(
                ['bash', run_script],
                cwd=target_case_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "status": "success",
                "message": "Case setup completed successfully",
                "output": result.stdout
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error_message": f"sub.sh execution failed: {e.stderr}",
                "exit_code": e.returncode
            }
    else:
        run_script = os.path.join(target_case_dir, 'set.sh')
        if not os.path.isfile(run_script):
            return {
                "status": "error",
                "error_message": "set.sh script not found in target directory"
            }
        try:
            result = subprocess.run(
                ['bash', run_script],
                cwd=target_case_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "status": "success",
                "message": "Case setup completed successfully",
                "output": result.stdout
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error_message": f"set.sh execution failed: {e.stderr}",
                "exit_code": e.returncode
            }



    

    

    
 
