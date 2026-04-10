import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import os.path

# 打印当前工作目录
print("当前工作目录:", os.getcwd())
# 打印当前脚本目录
print("当前脚本目录:", os.path.dirname(os.path.abspath(__file__)))

def evaluate_model(model_path, X_test, y_test):
    """
    评估单个模型的性能
    """
    try:
        # 加载模型
        model_data = joblib.load(model_path)
        
        # 检查模型数据的类型
        print(f"模型文件类型: {type(model_data)}")
        
        selected_features = None
        # 如果是字典，尝试提取model_pipeline
        if isinstance(model_data, dict):
            print(f"字典键: {list(model_data.keys())}")
            
            # 尝试提取model_pipeline
            if 'model_pipeline' in model_data:
                model = model_data['model_pipeline']
                selected_features = model_data.get('selected_features')
                print("成功从字典中提取model_pipeline")
            else:
                print("字典中没有model_pipeline键")
                return None, None, None, None, None
        else:
            # 不是字典，直接使用
            model = model_data
        
        # 训练阶段保存的是 200 维筛选特征，这里按同样索引子集化测试集
        X_input = X_test
        if selected_features:
            try:
                selected_idx = [int(i) for i in selected_features]
                X_input = X_test.iloc[:, selected_idx]
                print(f"使用 selected_features 进行预测，特征数量: {X_input.shape[1]}")
            except Exception as e:
                print(f"按 selected_features 切分特征失败: {str(e)}")
                return None, None, None, None, None

        # 检查模型是否有predict方法
        if hasattr(model, 'predict'):
            print("模型有predict方法")
            
            # 尝试预测
            try:
                y_pred = model.predict(X_input)
                
                # 计算评估指标
                mae = mean_absolute_error(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                r2 = r2_score(y_test, y_pred)
                
                return y_pred, mae, mse, rmse, r2
            except Exception as e:
                print(f"预测时出错: {str(e)}")
                
                # 尝试检查模型的n_features_in_属性
                if hasattr(model, 'n_features_in_'):
                    print(f"模型期望的特征数量: {model.n_features_in_}")
                    print(f"当前提供的特征数量: {X_input.shape[1]}")
                
                # 尝试检查流水线中的最后一个步骤
                if hasattr(model, 'steps'):
                    last_step = model.steps[-1][1]
                    if hasattr(last_step, 'n_features_in_'):
                        print(f"最后一个步骤期望的特征数量: {last_step.n_features_in_}")
                
                return None, None, None, None, None
        else:
            print("模型没有predict方法")
            return None, None, None, None, None
            
    except Exception as e:
        print(f"加载模型时出错: {model_path}, 错误: {str(e)}")
        return None, None, None, None, None

def main():
    # 使用绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 加载数据
    data_path = os.path.join(current_dir, 'data3.csv')
    features_path = os.path.join(current_dir, 'embedding_pro3.csv')
    
    print(f"数据文件路径: {data_path}, 存在: {os.path.exists(data_path)}")
    print(f"特征文件路径: {features_path}, 存在: {os.path.exists(features_path)}")
    
    data = pd.read_csv(data_path)
    features = pd.read_csv(features_path)
    
    # 使用实际列名作为目标变量
    y_uts = data['Strength (MPa)']  # 极限拉伸强度
    y_el = data['Elongation (%)']  # 延伸率
    
    X = features
    
    # 简单的训练测试拆分（可以根据需要调整）
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_el_train, y_el_test, y_uts_train, y_uts_test = train_test_split(
        X, y_el, y_uts, test_size=0.2, random_state=42
    )
    
    # 评估EL模型
    print("\n=== 评估延伸率 (EL) 模型 ===")
    # 使用绝对路径
    el_models = [
        os.path.join(current_dir, 'EL_models', 'alloy_model_GBR.pkl'),
        os.path.join(current_dir, 'EL_models', 'alloy_model_KNN.pkl'),
        os.path.join(current_dir, 'EL_models', 'alloy_model_LR.pkl'),
        os.path.join(current_dir, 'EL_models', 'alloy_model_RF.pkl'),
        os.path.join(current_dir, 'EL_models', 'alloy_model_SVR.pkl'),
        os.path.join(current_dir, 'EL_models', 'alloy_model_XGBoost.pkl')
    ]
    # 打印模型路径
    for model_path in el_models:
        print(f"检查模型路径: {model_path}, 存在: {os.path.exists(model_path)}")
    
    el_results = []
    for model_path in el_models:
        if os.path.exists(model_path):
            print(f"\n评估模型: {model_path}")
            y_pred, mae, mse, rmse, r2 = evaluate_model(model_path, X_test, y_el_test)
            if y_pred is not None:
                model_name = os.path.basename(model_path).replace('alloy_model_', '').replace('.pkl', '')
                el_results.append({
                    'model': model_name,
                    'MAE': mae,
                    'MSE': mse,
                    'RMSE': rmse,
                    'R²': r2
                })
                print(f"{model_name}: MAE={mae:.4f}, MSE={mse:.4f}, RMSE={rmse:.4f}, R²={r2:.4f}")
            else:
                print(f"跳过模型: {model_path}")
        else:
            print(f"模型文件不存在: {model_path}")
    
    # 评估UTS模型
    print("\n=== 评估极限拉伸强度 (UTS) 模型 ===")
    # 使用绝对路径
    uts_models = [
        os.path.join(current_dir, 'UTS_models', 'alloy_model_GBR.pkl'),
        os.path.join(current_dir, 'UTS_models', 'alloy_model_KNN.pkl'),
        os.path.join(current_dir, 'UTS_models', 'alloy_model_LR.pkl'),
        os.path.join(current_dir, 'UTS_models', 'alloy_model_RF.pkl'),
        os.path.join(current_dir, 'UTS_models', 'alloy_model_SVR.pkl'),
        os.path.join(current_dir, 'UTS_models', 'alloy_model_XGBoost.pkl')
    ]
    # 打印模型路径
    for model_path in uts_models:
        print(f"检查模型路径: {model_path}, 存在: {os.path.exists(model_path)}")
    
    uts_results = []
    for model_path in uts_models:
        if os.path.exists(model_path):
            print(f"\n评估模型: {model_path}")
            y_pred, mae, mse, rmse, r2 = evaluate_model(model_path, X_test, y_uts_test)
            if y_pred is not None:
                model_name = os.path.basename(model_path).replace('alloy_model_', '').replace('.pkl', '')
                uts_results.append({
                    'model': model_name,
                    'MAE': mae,
                    'MSE': mse,
                    'RMSE': rmse,
                    'R²': r2
                })
                print(f"{model_name}: MAE={mae:.4f}, MSE={mse:.4f}, RMSE={rmse:.4f}, R²={r2:.4f}")
            else:
                print(f"跳过模型: {model_path}")
        else:
            print(f"模型文件不存在: {model_path}")
    
    # 保存评估结果
    if el_results:
        pd.DataFrame(el_results).to_csv(os.path.join(current_dir, 'el_model_evaluation.csv'), index=False)
        print(f"EL模型评估结果已保存到: {os.path.join(current_dir, 'el_model_evaluation.csv')}")
    if uts_results:
        pd.DataFrame(uts_results).to_csv(os.path.join(current_dir, 'uts_model_evaluation.csv'), index=False)
        print(f"UTS模型评估结果已保存到: {os.path.join(current_dir, 'uts_model_evaluation.csv')}")
    
    # 可视化最佳模型的预测结果
    if el_results and uts_results:
        # 找到EL最佳模型
        best_el_model = max(el_results, key=lambda x: x['R²'])
        print(f"\nEL最佳模型: {best_el_model['model']}, R²={best_el_model['R²']:.4f}")
        
        # 找到UTS最佳模型
        best_uts_model = max(uts_results, key=lambda x: x['R²'])
        print(f"UTS最佳模型: {best_uts_model['model']}, R²={best_uts_model['R²']:.4f}")
        
        # 可视化预测结果
        plt.figure(figsize=(12, 6))
        
        # EL预测结果
        plt.subplot(1, 2, 1)
        best_el_model_path = os.path.join(current_dir, 'EL_models', f'alloy_model_{best_el_model["model"]}.pkl')
        y_el_pred, _, _, _, _ = evaluate_model(best_el_model_path, X_test, y_el_test)
        if y_el_pred is not None:
            plt.scatter(y_el_test, y_el_pred)
            plt.plot([y_el_test.min(), y_el_test.max()], [y_el_test.min(), y_el_test.max()], 'k--', lw=2)
            plt.xlabel('实际值')
            plt.ylabel('预测值')
            plt.title(f'EL最佳模型: {best_el_model["model"]}')
        
        # UTS预测结果
        plt.subplot(1, 2, 2)
        best_uts_model_path = os.path.join(current_dir, 'UTS_models', f'alloy_model_{best_uts_model["model"]}.pkl')
        y_uts_pred, _, _, _, _ = evaluate_model(best_uts_model_path, X_test, y_uts_test)
        if y_uts_pred is not None:
            plt.scatter(y_uts_test, y_uts_pred)
            plt.plot([y_uts_test.min(), y_uts_test.max()], [y_uts_test.min(), y_uts_test.max()], 'k--', lw=2)
            plt.xlabel('实际值')
            plt.ylabel('预测值')
            plt.title(f'UTS最佳模型: {best_uts_model["model"]}')
        
        plt.tight_layout()
        plt.savefig(os.path.join(current_dir, 'model_predictions.png'))
        print(f"预测结果可视化已保存到: {os.path.join(current_dir, 'model_predictions.png')}")
        plt.show()

if __name__ == "__main__":
    main()