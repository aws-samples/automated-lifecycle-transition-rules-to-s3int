# This script is intended to simplify the process of adding Intelligent Tiering Lifecycle Policies 
# to S3 buckets for all objects >128KB. See https://aws.amazon.com/s3/storage-classes/intelligent-tiering/ for
# details on Intelligent Tiering for S3 Buckets. 
# The Amazon S3 Intelligent-Tiering storage class is designed to optimize storage costs by automatically moving data to the most cost-effective access tier when access patterns change. 
# For a small monthly object monitoring and automation charge, S3 Intelligent-Tiering monitors access patterns and automatically moves objects that have not been accessed to lower cost access tiers. 
# S3 Intelligent-Tiering is the ideal storage class for data with unknown, changing, or unpredictable access patterns, independent of object size or retention period. 
# You can use S3 Intelligent-Tiering as the default storage class for data lakes, analytics, and new applications.  


import boto3
import pandas as pd
from datetime import datetime
from botocore.exceptions import ClientError
from time import strftime 
from tqdm import tqdm


s3 = boto3.client('s3')
now = datetime.now()
current_time = now.strftime("%H:%M:%S")
iam = boto3.resource('iam')
client = boto3.client('sts')

# method to determine accountID 
def getAccountID():
    account_id = client.get_caller_identity()
    return(account_id['Account'])
    #account_id = iam.CurrentUser().arn.split(':')[4]
    #return(account_id)

def main():
    listBuckets()
    createXls(TransitionStatus)

## Global list variable to keep track of the Bucket Name, Transition Days, StorageClass, Status  
TransitionStatus = []

# This method returns the LC policy. This policy will be used as the default LC policy 
# for the bucket with no LC policy and for the bucket with no "Transition policy" 
# Pass the name of the bucket with the method
def createLCP(Name):
    lcp = {
            'Rules': [
                {
                    'ID': "Added S3 INT Transition LC by automated script"+"-"+current_time,
                    'Filter': {},
                    'Status': 'Enabled',
                    'Transitions': [
                        {
                            'Days': 0,
                            'StorageClass': 'INTELLIGENT_TIERING'
                        },
                    ],
                    'NoncurrentVersionTransitions': [
                        {
                            'NoncurrentDays': 0,
                            'StorageClass': 'INTELLIGENT_TIERING'
                        },
                    ],
                }
            ]
        }
    return lcp

# This method tracks the LC policy associated with the bucket. It checks for 3 scenarios. 
# Scenario #1
# If an LC policy exist,  the script checks if it has a transition policy (with a StorageClass such as Glacier, S3-Infrequent access or even S3-Intelligent Tiering or others). 
# If the transition policy does not exist, the script will add a new policy to the existing policy with the transition set for the Current and Previous version to the INT StorageClass with “0” days using createLCP(Name) 
# and records the action in the global list variable - TransitionStatus with the status = 'updated existing LC Policy'
#Scenario #2
# If an LC policy exist and has a transition policy (to move to a different StorageClass such as Glacier, S3-Infrequent access or others), the script  records its action action in the excel sheet and take no action on the LC policy.
# It just records - transition storage and days to transition in the global list variable - TransitionStatus with the status = 'No Changes LC Policy'
# Scenario #3
#   If no LC policy is attached to the bucket, the script adds a new policy with the transition set for the Current and Previous version to the INT StorageClass with “0” days. 
# It records its action in the excel sheet in the global list variable with the TransitionStatus = 'Added LC Policy'

# Policy Dictionary to track LC policy of the bucket
policy = {}
def createOrUpdateLCP(Name):
    ownerAccountId = getAccountID()
    try:
        result = s3.get_bucket_lifecycle_configuration(Bucket=Name, ExpectedBucketOwner=ownerAccountId)
        Rules= result['Rules']
        # Scenario #1 
        if any("Transitions" in keys for keys in Rules):
            for Rule in Rules:
                for key, value in Rule.items():
                    if (key == 'Transitions'):
                        Days = value[0]['Days']
                        StorageClass = value[0]['StorageClass']
                        TransitionStatus.append(Name)
                        TransitionStatus.append(Days)
                        TransitionStatus.append(StorageClass)
                        TransitionStatus.append('No changes made to S3 Lifecycle configuration')
        else:
            # Scenario #2
            policy = createLCP(Name)
            for p in policy['Rules']:
                for key, value in p.items():
                    if key =='Transitions':
                        Days = value[0]['Days']
                        StorageClass = value[0]['StorageClass']
                        TransitionStatus.append(Name)
                        TransitionStatus.append(Days)
                        TransitionStatus.append(StorageClass)
                        TransitionStatus.append('Updated the existing Lifecycle with Transition rule to S3 INT')

            Rules.append(policy['Rules'][0])
            lcp = s3.put_bucket_lifecycle_configuration(
                Bucket=Name, LifecycleConfiguration = {'Rules':Rules })
    except ClientError as err:
        # Scenario #3
        # Catching a situation where bucket does not belong to an account
        print (err.response['Error']['Code'])
        if err.response['Error']['Code'] == 'AccessDenied':
            print ("This account does not own the bucket {}.".format(Name))
            Days = 'N/A'
            StorageClass ='N/A'
            TransitionStatus.append(Name)
            TransitionStatus.append(Days)
            TransitionStatus.append(StorageClass)
            TransitionStatus.append("The Bucket "+Name+" does not belong to the account-"+ownerAccountId)
        elif err.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
            print("This bucket {} has no LifeCycle Configuration".format(Name)) 
            policy = createLCP(Name)
            for p in policy['Rules']:
                for key, value in p.items():
                    if key =='Transitions':
                        Days = value[0]['Days']
                        StorageClass = value[0]['StorageClass']
                        TransitionStatus.append(Name)
                        TransitionStatus.append(Days)
                        TransitionStatus.append(StorageClass)
                        TransitionStatus.append('Added a new S3 Lifecycle Transition Rule to S3 INT')
            lcp = s3.put_bucket_lifecycle_configuration(
                    Bucket=Name, LifecycleConfiguration = policy)
        else:
            print ("err.response['Error']['Code']")

# listBuckets - lists the buckets per region and check each bucket policy using createOrUpdateLCP() method  
def listBuckets():
    BucketName = s3.list_buckets()
    for bucket in tqdm(BucketName['Buckets']):
        Name = bucket['Name'] 
        createOrUpdateLCP(Name)
            
# createXls - create XLS sheet of the transitionStatus detail. The file name is "transitionStatus-HHMMSS.xlsx" where HHMMSS is the current time in hours, minutes, and seconds
def createXls(list):
    currenttime = now.strftime("%H%M%S")
    filename = "transitionStatus"+"-"+currenttime+".xlsx"
    print("Results are available in ./" + filename + ".")
    df = pd.DataFrame()
    df['BucketName'] = list[0::4]
    df['Days'] = list[1::4]
    df['StorageClass'] = list[2::4]
    df['TransitionStatus'] = list[3::4]
    df.to_excel(filename, index = False)

if __name__ == "__main__":
    main()