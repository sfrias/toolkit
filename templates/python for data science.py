#Albert Sanchez Lafuente 2/4/2019, Pineda de Mar, Spain
#https://github.com/albertsl/
#Structure of the template mostly based on the Appendix B of the book Hands-on Machine Learning with Scikit-Learn and TensorFlow by Aurelien Geron (https://amzn.to/2WIfsmk)
#Big thank you to Uxue Lazcano (https://github.com/uxuelazkano) for code on model comparison
#Load packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
sns.set()

#Load data
df = pd.read_csv('file.csv')
#If data is too big, take a sample of it
df = pd.read_csv('file.csv', nrows=50000)
#Reduce dataframe memory usage
def reduce_mem_usage(df):
	""" iterate through all the columns of a dataframe and modify the data type
		to reduce memory usage.        
	"""
	start_mem = df.memory_usage().sum() / 1024**2
	print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))
	
	for col in df.columns:
		col_type = df[col].dtype
		
		if col_type != object:
			c_min = df[col].min()
			c_max = df[col].max()
			if str(col_type)[:3] == 'int':
				if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
					df[col] = df[col].astype(np.int8)
				elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
					df[col] = df[col].astype(np.int16)
				elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
					df[col] = df[col].astype(np.int32)
				elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
					df[col] = df[col].astype(np.int64)  
			else:
				if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
					df[col] = df[col].astype(np.float16)
				elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
					df[col] = df[col].astype(np.float32)
				else:
					df[col] = df[col].astype(np.float64)
		else:
			df[col] = df[col].astype('category')

	end_mem = df.memory_usage().sum() / 1024**2
	print('Memory usage after optimization is: {:.2f} MB'.format(end_mem))
	print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))
	
	return df

#Check for missing data
total_null = df.isna().sum().sort_values(ascending=False)
percent = 100*(df.isna().sum()/df.isna().count()).sort_values(ascending=False)
missing_data = pd.concat([total_null, percent], axis=1, keys=['Total', 'Percent'])
#Generate new features with missing data
df['feature1_nan'] = df['feature1'].isna()
df['feature2_nan'] = df['feature2'].isna()
#Also look for infinite data, recommended to check it also after feature engineering
df.replace(np.inf,0,inplace=True)
df.replace(-np.inf,0,inplace=True)

#Check for duplicated data
df.duplicated().value_counts()
df['duplicated'] = df.duplicated() #Create a new feature

#Fill missing data or drop columns/rows
df.fillna()
df.drop('column_full_of_nans')
df.dropna(how='any', inplace=True)

#Visualize data
df.head()
df.describe()
df.info()
df.columns
#For a categorical dataset we want to see how many instances of each category there are
df['categorical_var'].value_counts()

#Exploratory Data Analysis (EDA)
sns.pairplot(df)
sns.distplot(df['column'])
sns.countplot(df['column'])

#Fix or remove outliers
sns.boxplot(df['feature1'])
sns.boxplot(df['feature2'])

#Correlation analysis
sns.heatmap(df.corr(), annot=True, fmt='.2f')
correlations = df.corr().abs().unstack().sort_values(kind="quicksort").reset_index()
correlations = correlations[correlations['level_0'] != correlations['level_1']]

#Encode categorical variables
#Encoding for target variable
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['categorical_var'] = le.fit_transform(df['categorical_var'])
#One hot encoding for categorical information
#Use sklearn's OneHotEncoder for categories encoded as possitive real numbers
from sklearn.preprocessing import OneHotEncoder
enc = OneHotEncoder()
df['var_to_encode'] = enc.fit_transform(df['var_to_encode'])
#Use pandas get_dummies for categories encoded as strings
pd.get_dummies(df, columns=['col1','col2'])

#Feature selection: Drop attributes that provide no useful information for the task

#Feature engineering. Create new features by transforming the data
#Discretize continuous features
#Decompose features (categorical, date/time, etc.)
#Add promising transformations of features (e.g., log(x), sqrt(x), x^2, etc.)
#Aggregate features into promising new features (x*y)
#For speed/movement data, add vectorial features. Try many different combinations
df['position_norm'] = df['position_X'] ** 2 + df['position_Y'] ** 2 + df['position_Z'] ** 2
df['position_module'] = df['position_norm'] ** 0.5
df['position_norm_X'] = df['position_X'] / df['position_module']
df['position_norm_Y'] = df['position_Y'] / df['position_module']
df['position_norm_Z'] = df['position_Z'] / df['position_module']
df['position_over_velocity'] = df['position_module'] / df['velocity_module']
#For time series data: Discretize the data by different samples.
from astropy.stats import median_absolute_deviation
from statsmodels.robust.scale import mad
from scipy.stats import kurtosis
from scipy.stats import skew

def CPT5(x):
	den = len(x)*np.exp(np.std(x))
	return sum(np.exp(x))/den

def SSC(x):
	x = np.array(x)
	x = np.append(x[-1], x)
	x = np.append(x, x[1])
	xn = x[1:len(x)-1]
	xn_i2 = x[2:len(x)]    # xn+1
	xn_i1 = x[0:len(x)-2]  # xn-1
	ans = np.heaviside((xn-xn_i1)*(xn-xn_i2), 0)
	return sum(ans[1:])

def wave_length(x):
	x = np.array(x)
	x = np.append(x[-1], x)
	x = np.append(x, x[1])
	xn = x[1:len(x)-1]
	xn_i2 = x[2:len(x)]    # xn+1
	return sum(abs(xn_i2-xn))

def norm_entropy(x):
	tresh = 3
	return sum(np.power(abs(x), tresh))

def SRAV(x):
	SRA = sum(np.sqrt(abs(x)))
	return np.power(SRA/len(x), 2)

def mean_abs(x):
	return sum(abs(x))/len(x)

def zero_crossing(x):
	x = np.array(x)
	x = np.append(x[-1], x)
	x = np.append(x, x[1])
	xn = x[1:len(x)-1]
	xn_i2 = x[2:len(x)]    # xn+1
	return sum(np.heaviside(-xn*xn_i2, 0))

df_tmp = pd.DataFrame()
for column in tqdm(df.columns):
	df_tmp[column + '_mean'] = df.groupby(['series_id'])[column].mean()
	df_tmp[column + '_median'] = df.groupby(['series_id'])[column].median()
	df_tmp[column + '_max'] = df.groupby(['series_id'])[column].max()
	df_tmp[column + '_min'] = df.groupby(['series_id'])[column].min()
	df_tmp[column + '_std'] = df.groupby(['series_id'])[column].std()
	df_tmp[column + '_range'] = df_tmp[column + '_max'] - df_tmp[column + '_min']
	df_tmp[column + '_max_over_Min'] = df_tmp[column + '_max'] / df_tmp[column + '_min']
	df_tmp[column + 'median_abs_dev'] = df.groupby(['series_id'])[column].mad()
	df_tmp[column + '_mean_abs_chg'] = df.groupby(['series_id'])[column].apply(lambda x: np.mean(np.abs(np.diff(x))))
	df_tmp[column + '_mean_change_of_abs_change'] = df.groupby('series_id')[column].apply(lambda x: np.mean(np.diff(np.abs(np.diff(x)))))
	df_tmp[column + '_abs_max'] = df.groupby(['series_id'])[column].apply(lambda x: np.max(np.abs(x)))
	df_tmp[column + '_abs_min'] = df.groupby(['series_id'])[column].apply(lambda x: np.min(np.abs(x)))
	df_tmp[column + '_abs_avg'] = (df_tmp[column + '_abs_min'] + df_tmp[column + '_abs_max'])/2
	df_tmp[column + '_abs_mean'] = df.groupby('series_id')[column].apply(lambda x: np.mean(np.abs(x)))
	df_tmp[column + '_abs_std'] = df.groupby('series_id')[column].apply(lambda x: np.std(np.abs(x)))
	df_tmp[column + '_abs_range'] = df_tmp[column + '_abs_max'] - df_tmp[column + '_abs_min']
	df_tmp[column + '_skew'] = df.groupby(['series_id'])[column].skew()
	df_tmp[column + '_q25'] = df.groupby(['series_id'])[column].quantile(0.25)
	df_tmp[column + '_q75'] = df.groupby(['series_id'])[column].quantile(0.75)
	df_tmp[column + '_q95'] = df.groupby(['series_id'])[column].quantile(0.95)
	df_tmp[column + '_iqr'] = df_tmp[column + '_q75'] - df_tmp[column + '_q25']
	df_tmp[column + '_CPT5'] = df.groupby(['series_id'])[column].apply(CPT5)
	df_tmp[column + '_SSC'] = df.groupby(['series_id'])[column].apply(SSC)
	df_tmp[column + '_wave_lenght'] = df.groupby(['series_id'])[column].apply(wave_length)
	df_tmp[column + '_norm_entropy'] = df.groupby(['series_id'])[column].apply(norm_entropy)
	df_tmp[column + '_SRAV'] = df.groupby(['series_id'])[column].apply(SRAV)
	df_tmp[column + '_kurtosis'] = df.groupby(['series_id'])[column].apply(kurtosis)
	df_tmp[column + '_zero_crossing'] = df.groupby(['series_id'])[column].apply(zero_crossing)
	df_tmp[column +  '_unq'] = df[column].round(3).nunique()
	try:
		df_tmp[column + '_freq'] = df[column].value_counts().idxmax()
	except:
		df_tmp[column + '_freq'] = 0
	df_tmp[column + '_max_freq'] = df[df[column] == df[column].max()].shape[0]
	df_tmp[column + '_min_freq'] = df[df[column] == df[column].min()].shape[0]
	df_tmp[column + '_pos_freq'] = df[df[column] >= 0].shape[0]
	df_tmp[column + '_neg_freq'] = df[df[column] < 0].shape[0]
	df_tmp[column + '_nzeros'] = (df[column]==0).sum(axis=0)
df = df_tmp.copy()
#Create a new column from conditions on other columns
df['column_y'] = df[(df['column_x1'] | 'column_x2') & 'column_x3']
df['column_y'] = df['column_y'].apply(bool)
df['column_y'] = df['column_y'].apply(int)
#Create a new True/False column according to the first letter on another column.
lEI = [0] * df.shape[0]

for i, row in df.iterrows():
	try:
		l = df['room_list'].iloc[i].split(', ')
	except:
		#When the given row is empty
		l = []
	for element in l:
		if element[0] == 'E' or element[0] == 'I':
			lEI[i] = 1

df['EI'] = pd.Series(lEI)

#Scaling features
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(df)
df_norm = pd.DataFrame(scaler.transform(df), columns=df.columns)

#Apply all the same transformations to the test set

#Define Validation method
#Train and validation set split
from sklearn.model_selection import train_test_split
X = df.drop('target_var', axis=1)
y = df['column to predict']
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size = 0.4, stratify = y.values, random_state = 101)
#Cross validation
from sklearn.model_selection import cross_val_score
cross_val_score(model, X, y, cv=5)
#StratifiedKFold
from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5, random_state=101)
for train_index, val_index in skf.split(X, y):
	X_train, X_val = X[train_index], X[val_index]
	y_train, y_val = y[train_index], y[val_index]


#Train many quick and dirty models from different categories(e.g., linear, naive Bayes, SVM, Random Forests, neural net, etc.) using standard parameters.
#########
# Linear Regression
#########
from sklearn.linear_model import LinearRegression
lr = LinearRegression()
lr.fit(X_train,y_train)

#Linear model interpretation
lr.intercept_
lr.coef_

#Use model to predict
y_pred = lr.predict(X_val)

#Evaluate accuracy of the model
plt.scatter(y_val, y_pred) #should have the shape of a line for good predictions
sns.distplot(y_val - y_pred) #should be a normal distribution centered at 0
acc_lr = round(lr.score(X_val, y_val) * 100, 2)

#########
# Logistic Regression
#########
from sklearn.linear_model import LogisticRegression
logmodel = LogisticRegression()
logmodel.fit(X_train,y_train)

#Use model to predict
y_pred = logmodel.predict(X_val)

#Evaluate accuracy of the model
acc_log = round(logmodel.score(X_val, y_val) * 100, 2)

#########
# KNN
#########
from sklearn.neighbors import KNeighborsClassifier
knn = KNeighborsClassifier(n_neighbors = 5)
knn.fit(X_train, y_train)

#Use model to predict
y_pred = knn.predict(X_val)

#Evaluate accuracy of the model
acc_knn = round(knn.score(X_val, y_val) * 100, 2)

#########
# Decision Tree
#########
from sklearn.tree import DecisionTreeClassifier
dtree = DecisionTreeClassifier()
dtree.fit(X_train, y_train)

#Use model to predict
y_pred = dtree.predict(X_val)

#Evaluate accuracy of the model
acc_dtree = round(dtree.score(X_val, y_val) * 100, 2)

#########
# Random Forest
#########
from sklearn.ensemble import RandomForestClassifier
rfc = RandomForestClassifier(n_estimators=200, random_state=101, n_jobs=-1, verbose=3)
rfc.fit(X_train, y_train)

from sklearn.ensemble import RandomForestRegressor
rfr = RandomForestRegressor(n_estimators=200, random_state=101, n_jobs=-1, verbose=3)
rfr.fit(X_train, y_train)

#Use model to predict
y_pred = rfr.predict(X_val)

#Evaluate accuracy of the model
acc_rf = round(rfr.score(X_val, y_val) * 100, 2)

#Evaluate feature importance
importances = rfr.feature_importances_
std = np.std([importances for tree in rfr.estimators_], axis=0)
indices = np.argsort(importances)[::-1]

feature_importances = pd.DataFrame(rfr.feature_importances_, index = X_train.columns, columns=['importance']).sort_values('importance', ascending=False)
feature_importances.sort_values('importance', ascending=False)

plt.figure()
plt.title("Feature importances")
plt.bar(range(X_train.shape[1]), importances[indices], yerr=std[indices], align="center")
plt.xticks(range(X_train.shape[1]), indices)
plt.xlim([-1, X_train.shape[1]])
plt.show()

#########
# lightGBM (LGBM)
#########
import lightgbm as lgb
# create dataset for lightgbm
lgb_train = lgb.Dataset(X_train, y_train)
lgb_eval = lgb.Dataset(X_val, y_val, reference=lgb_train)

# specify your configurations as a dict
params = {
	'boosting_type': 'gbdt',
	'objective': 'regression',
	'metric': {'l2', 'l1'},
	'num_leaves': 31,
	'learning_rate': 0.05,
	'feature_fraction': 0.9,
	'bagging_fraction': 0.8,
	'bagging_freq': 5,
	'verbose': 0
}

# train
gbm = lgb.train(params, lgb_train, num_boost_round=20, valid_sets=lgb_eval, early_stopping_rounds=5)

# save model to file
gbm.save_model('model.txt')

# predict
y_pred = gbm.predict(X_val, num_iteration=gbm.best_iteration)

#########
# XGBoost
#########
import xgboost as xgb

params = {'objective': 'multi:softmax',  # Specify multiclass classification
		'num_class': 9,  # Number of possible output classes
		'tree_method': 'hist',  # Use gpu_hist for GPU accelerated algorithm.
		'eta': 0.1,
		'max_depth': 6,
		'silent': 1,
		'gamma': 0,
		'eval_metric': "merror",
		'min_child_weight': 3,
		'max_delta_step': 1,
		'subsample': 0.9,
		'colsample_bytree': 0.4,
		'colsample_bylevel': 0.6,
		'colsample_bynode': 0.5,
		'lambda': 0,
		'alpha': 0,
		'seed': 0}

xgtrain = xgb.DMatrix(X_train, label=y_train)
xgval = xgb.DMatrix(X_val, label=y_val)
xgtest = xgb.DMatrix(X_test)

num_rounds = 500
gpu_res = {}  # Store accuracy result
# Train model
xgbst = xgb.train(params, xgtrain, num_rounds, evals=[
			(xgval, 'test')], evals_result=gpu_res)

y_pred = xgbst.predict(xgtest)

#########
# Support Vector Machine (SVM)
#########
from sklearn.svm import SVC
model = SVC()
model.fit(X_train, y_train)

#Use model to predict
y_pred = model.predict(X_val)

#Evaluate accuracy of the model
acc_svm = round(model.score(X_val, y_val) * 100, 2)

#########
# K-Means Clustering
#########
#Train model
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=K) #Choose K
kmeans.fit(df)
#Evaluate the model
kmeans.cluster_centers_
kmeans.labels_

#Measure and compare their performance
models = pd.DataFrame({
'Model': ['Linear Regression', 'Support Vector Machine', 'KNN', 'Logistic Regression', 
			'Random Forest'],
'Score': [acc_lr, acc_svm, acc_knn, acc_log, 
			acc_rf]})
models.sort_values(by='Score', ascending=False)
#Analyze the most significant variables for each algorithm.
#Analyze the types of errors the models make.
#What data would a human have used to avoid these errors?
#Have a quick round of feature selection and engineering.
#Have one or two more quick iterations of the five previous steps.
#Short-list the top three to five most promising models, preferring models that make different types of errors.
#Define Performance Metrics
#ROC AUC for classification tasks
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve
roc_auc = roc_auc_score(y_val, model.predict(X_val))
fpr, tpr, thresholds = roc_curve(y_val, model.predict_proba(X_val)[:,1])
plt.figure()
plt.plot(fpr, tpr, label='Model (area = %0.2f)' % roc_auc)
plt.plot([0, 1], [0, 1],'r--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic')
plt.legend(loc="lower right")
plt.show()
#Confusion Matrix
from sklearn.metrics import confusion_matrix
confusion_matrix(y_val, y_pred)
#MAE, MSE, RMSE
from sklearn import metrics
metrics.mean_absolute_error(y_val, y_pred)
metrics.mean_squared_error(y_val, y_pred)
np.sqrt(metrics.mean_squared_error(y_val, y_pred))
#Classification report
from sklearn.metrics import classification_report
print(classification_report(y_val,y_pred))

#Fine-tune the hyperparameters using cross-validation
#Treat your data transformation choices as hyperparameters, especially when you are not sure about them (e.g., should I replace missing values with zero or with the median value? Or just drop the rows?)
#Unless there are very few hyperparameter values to explore, prefer random search over grid search. If training is very long, you may prefer a Bayesian optimization approach
from sklearn.model_selection import GridSearchCV
param_grid = {'C':[0.1,1,10,100,1000], 'gamma':[1,0.1,0.01,0.001,0.0001]}
grid = GridSearchCV(model, param_grid, verbose = 3)
grid.fit(X_train, y_train)
grid.best_params_
grid.best_estimator_

#Try Ensemble methods. Combining your best models will often perform better than running them individually

#Once you are confident about your final model, measure its performance on the test set to estimate the generalization error
