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
    return(account_id['829127864189'])
    #account_id = iam.CurrentUser().arn.split(':')[4]
    #return(account_id)

def main():
    listBuckets()
    createXls(TransitionStatus)
    
def createLCP(Lifecycle.Test):
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

policy = {}
def createOrUpdateLCP(Name):
    ownerAccountId = getAccountID()
    try:
        result = s3.get_bucket_lifecycle_configuration(Bucket=Name, ExpectedBucketOwner=829127864189)
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
