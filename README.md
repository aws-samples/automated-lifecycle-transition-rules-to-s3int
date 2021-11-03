# S3Lifecycle to move the objects from the buckets in STD storage class to INT storage class.

This script is intended to simplify the process of adding Intelligent Tiering Lifecycle Policies to S3 buckets for all objects >128KB. See https://aws.amazon.com/s3/storage-classes/intelligent-tiering/ for details on Intelligent Tiering for S3 Buckets. The Amazon S3 Intelligent-Tiering storage class is designed to optimize storage costs by automatically moving data to the most cost-effective access tier when access patterns change. 
For a small monthly object monitoring and automation charge, S3 Intelligent-Tiering monitors access patterns and automatically moves objects that have not been accessed to lower cost access tiers. S3 Intelligent-Tiering is the ideal storage class for data with unknown, changing, or unpredictable access patterns, independent of object size or retention period. You can use S3 Intelligent-Tiering as the default storage class for data lakes, analytics, and new applications. 


## This code allows you to move the buckets from the S3 STD to S3 INT cross-region in an account. ##

Disclaimer: This is a sample code that has been tested in a non-production account. I highly recommend testing before using on production buckets.
 =================
 Attached code was tested and validated on my account, which has a few buckets across regions, using best practices and documentation from here - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_bucket_lifecycle_configuration. You will need to own modifying it for your use case. This code and content herein does not constitute an endorsement, attestation or validation of your use case, but is intended for informational purposes only.
 

# Scenario #1 -  
If an LC policy exist and has a transition policy (with a StorageClass such as Glacier, S3-Infrequent access or even S3-Intelligent Tiering or others), the script records its action in the excel sheet with the status = 'No Changes LC Policy'
# Scenario #2 -
If an LC policy exist, the script checks if it has a transition policy (with a StorageClass such as Glacier, S3-Infrequent access or even S3-Intelligent Tiering or others). If the transition policy does not exist, the script will add a new policy to the existing policy with the transition set for the current and previous version to the INT StorageClass with “0” days. It also records its action in the excel sheet with the status = 'updated existing LC policy with Transition to S3 INT'
# Scenario #3
If no LC policy attached to the bucket, the script adds a new policy with the transition set for the current and previous version to the INT StorageClass with “0” days. It records its action in the excel sheet with the status = 'Added an LC to Transition to S3 INT'

Save the requirements.txt file in the same directory as the python script S3LC.py. You may want to run the requirements.txt file if you don't have appropriate dependency to run the python script. You can run using below command- 

**pip3 install -r requirements.txt**

#here is the command to script -

**python3 S3LC.py**
