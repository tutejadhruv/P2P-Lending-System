# -*- coding: utf-8 -*-
"""P2P Lending.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1upuzWKzt5hvsgL2Rmg7TJi5wcn37VIH1

### P2P Lending System

### Library Imports
"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense,Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from statsmodels.stats.outliers_influence import variance_inflation_factor

# %matplotlib inline

"""### Data Import"""

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials

# Authenticate and create the PyDrive client.
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

link = "https://drive.google.com/file/d/1aGf9sDBY0-7UAsO2l7w9lxKBtO954bv4/view?usp=sharing"
id = "1aGf9sDBY0-7UAsO2l7w9lxKBtO954bv4"

downloaded = drive.CreateFile({'id':id}) 
downloaded.GetContentFile('Master_Loan_Summary.csv')  
df = pd.read_csv('Master_Loan_Summary.csv')
# Dataset is now stored in a Pandas Dataframe

"""### EDA"""

df.head()

df.shape

df['loan_status_description'].value_counts()

"""**Countplot of Target Varaible**"""

plt.figure(figsize=(10,6))
sns.countplot(x='loan_status_description', data=df, palette='Set1')

"""**Histogram of amount_borrowed**"""

plt.figure(figsize=(12,5))
ax = sns.histplot(data=df, x='amount_borrowed',bins=50, color='olive')
ax.set(xlabel='Loan Amount', ylabel='Frequency')
plt.show()

"""**Correlation Heatmap**"""

plt.figure(figsize=(12,8))
sns.heatmap(df.corr(), annot=True, linewidths=0.5)

"""
**intallment - amount_borrowed plot**"""

sns.scatterplot(x='installment', y='amount_borrowed', data=df)

"""**loan_status_prediction - amount_borrowed box plot**"""

sns.boxplot(x='loan_status_description', y='amount_borrowed', data=df)

"""**Grade Count Plot**"""

grade_order = sorted(df['grade'].unique())
plt.figure(figsize=(12,8))
sns.countplot(x='grade', data=df, hue='loan_status_description', order=grade_order)

"""**Data Source Count Plot**"""

plt.figure(figsize=(9,5))
sns.countplot(x='data_source', data=df, hue='loan_status_description')

"""### Data Processing"""

df.head()

"""**Dropping Rows with Completed and Current loan_status_description**

Here, I will remove the current and cancelled, as we can predict whether the current and cancelled loans would fall into completed, current or defaulted category.
"""

df = df[((df['loan_status_description'] != 'CURRENT') & (df['loan_status_description'] != 'CANCELLED'))]

df['loan_status_description'].value_counts()

"""**Converting loan_status_description (String) to numerical**"""

df['loan_status_description'] = df['loan_status_description'].map({'COMPLETED':0, 'CHARGEOFF':1, 'DEFAULTED':2})

df['loan_status_description'].value_counts()

"""**Checking Null Values**"""

df.isnull().sum()

"""**Checking Null Value Percentage**"""

(df.isnull().sum()/df.shape[0])*100

"""**Handling Null Values of listing_title Feature**

Here we will consider all Null values in listing_title as 'other'.
"""

df['listing_title'].value_counts()

df['listing_title'].fillna(value = 'other', inplace = True)

df['listing_title'].value_counts()

df.isnull().sum()

"""**Dataset Categorical Columns**"""

df.dtypes[df.dtypes == object]

"""Here we will drop loan origination_date, as we do not know yet if the loan is approved or not.

Also, we will be removing last_payment_date because every loan can have same or different dates, and it will not help in categorizing loan_status_description.

next_payment_due_date will be no use if loan_status is completed, defaulted or charged_off
"""

df.drop(columns=['origination_date', 'last_payment_date', 'next_payment_due_date'], inplace=True)

"""**Converting grade, listing_title, data_source into dummy variable**"""

df = pd.get_dummies(df, columns = ['grade', 'listing_title', 'data_source'], drop_first = True)

df.head()

"""**Dataset Continous Variables**

Every loan has a unique loan_number, and can be removed.
"""

df.drop('loan_number', inplace=True, axis=1)

"""**Converting term into dummy variable**"""

df.term.value_counts()

"""As term has only three values, it can be converted to dummy variable."""

df = pd.get_dummies(df, columns=['term'], drop_first=True)

df.head()

"""**Multicollinearity Check with VIF on Continous Variables**"""

def calc_vif(X):

    # Calculating VIF
    vif = pd.DataFrame()
    vif["variables"] = X.columns
    vif["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]

    return(vif)

# VIF Multicollinearity check
X = df[['amount_borrowed', 'borrower_rate',
       'installment', 'principal_balance', 'principal_paid', 'interest_paid',
       'late_fees_paid', 'debt_sale_proceeds_received', 'days_past_due']]
vif = calc_vif(X)
vif[vif['VIF']>10]

"""Here I have take VIF threshold = 10. Given the above result, I am removing amount_borrowed which has highest VIF and run VIF again."""

X.drop('amount_borrowed', axis = 1, inplace = True)

vif = calc_vif(X)
vif[vif['VIF']>10]

"""Now, removing installment and checking VIF again."""

X.drop('installment', axis = 1, inplace= True)
vif = calc_vif(X)
vif[vif['VIF']>10]

"""Now, df continous variables have no feature having VIF > 10.

### Model Building

**Neural Network Model**
"""

# Removing amount_borrowed, installment from df
df.drop(['installment', 'amount_borrowed'], axis = 1, inplace= True)

df.head()

X = df.drop('loan_status_description', axis = 1)
y = df['loan_status_description']

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=101)

# Normalising dataset
scaler = MinMaxScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

X.shape

# Building Neural Network Model
model = Sequential()

# Adding Input Layer
model.add(Dense(29, activation='relu'))
model.add(Dropout(0.2)) # This will help in regularization

# Hidden Layer
model.add(Dense(14, activation='relu'))
model.add(Dropout(0.2))

# Hidden Layer
model.add(Dense(7, activation='relu'))
model.add(Dropout(0.2))

# Output Layer. 
model.add(Dense(3, activation='softmax'))

# Compile Model
model.compile(loss='categorical_crossentropy', optimizer='adam')

y_train_model = pd.get_dummies(y_train)
y_test_model = pd.get_dummies(y_test)

early_stop = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=10)

# Model with activation = 'softmax', loss = 'categorical_crossentropy'
model.fit(x=X_train, y=y_train_model, epochs=50, validation_data=(X_test, y_test_model), batch_size = 256)

# Loss Comparison between training and test
losses = pd.DataFrame(model.history.history)
losses.plot()

# Predictions
predictions = pd.DataFrame(model.predict_classes(X_test))

print(confusion_matrix(y_test, predictions))

print(classification_report(y_test, predictions))

"""**Random Forest Model**"""

rfc = RandomForestClassifier(n_estimators=100, max_depth = None)
rfc.fit(X_train, y_train)



rfc_pred = rfc.predict(X_test)

print(confusion_matrix(y_test,rfc_pred))

print(classification_report(y_test,rfc_pred))