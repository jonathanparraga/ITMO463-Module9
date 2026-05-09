// Basic ExpressJS hello world.
const express = require('express')
const app = express();
const multer = require("multer");
const multerS3 = require("multer-s3");

const { 
  S3Client, 
  ListBucketsCommand, 
  ListObjectsCommand, 
  GetObjectCommand 
} = require('@aws-sdk/client-s3');

const {
  SecretsManagerClient,
  ListSecretsCommand,
  GetSecretValueCommand,
} = require("@aws-sdk/client-secrets-manager"); // CommonJS import

const {
  SNSClient,
  ListTopicsCommand,
  GetTopicAttributesCommand,
  SubscribeCommand,
  PublishCommand,
} = require("@aws-sdk/client-sns");

const {
  RDSClient,
  DescribeDBInstancesCommand,
} = require("@aws-sdk/client-rds");

const {
  SQSClient,
  GetQueueUrlCommand,
  SendMessageCommand,
  ListQueuesCommand,
} = require("@aws-sdk/client-sqs");

const { v4: uuidv4 } = require("uuid");
//////////////////////////////////////////////////////////////////////////////
// Change this to match YOUR default REGION
//////////////////////////////////////////////////////////////////////////////
const REGION = "us-east-2"; //e.g. "us-east-1";
const s3 = new S3Client({ region: REGION });
///////////////////////////////////////////////////////////////////////////
// I hardcoded my S3 bucket name, this you need to determine dynamically
// Using the AWS JavaScript SDK
///////////////////////////////////////////////////////////////////////////
//var bucketName = '';
//listBuckets().then(result =>{bucketName = result;}).catch(err=>{console.error("listBuckets function call failed.")});
//	var upload = multer({
//        storage: multerS3({
//        s3: s3,
//        bucket: bucketName,
//        key: function (req, file, cb) {
//            cb(null, file.originalname);
//            }
//    })
//	});

//////////////////////////////////////////////////////////
// Add S3 ListBucket code
//
let rawBucketName = "";

const listBuckets = async () => {
  if (rawBucketName) {
    return rawBucketName;
  }

  const client = new S3Client({ region: REGION });
  const command = new ListBucketsCommand({});

  try {
    const results = await client.send(command);

    for (const element of results.Buckets) {
      if (element.Name.includes("raw")) {
        console.log("RAW bucket found:", element.Name);
        rawBucketName = element.Name;
        return rawBucketName;
      }
    }

    throw new Error("No raw bucket found.");
  } catch (err) {
    console.error(err);
    throw err;
  }
};

var upload = multer({
  storage: multerS3({
    s3: s3,
    bucket: function (req, file, cb) {
      listBuckets()
        .then((bucketName) => cb(null, bucketName))
        .catch((err) => cb(err));
    },
    key: function (req, file, cb) {
      cb(null, file.originalname);
    }
  })
});
//-------------------------------------------

///////////////////////////////////////
// ListObjects S3 
// https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/clients/client-s3/interfaces/listobjectscommandoutput.html
// 
const listObjects = async (req, res) => {
  const client = new S3Client({ region: REGION });
  const bucketName = await listBuckets();
  const command = new ListObjectsCommand({ Bucket: bucketName });

  try {
    const results = await client.send(command);
    console.log("List Objects Results: ", results);
    const url = [];
    const contents = results.Contents || [];

    for (let i = 0; i < contents.length; i++) {
      url.push("https://" + results.Name + ".s3.amazonaws.com/" + contents[i].Key);
    }

    console.log("URL: ", url);
    return url;
  } catch (err) {
    console.error(err);
    throw err;
  }
};


///////////////////////////////////////////////
/// Get posted data as an async function
//
const getPostedData = async (req, res) => {
  try {
										 
    let s3URL = req.files[0].location;
    if (!s3URL) {
      s3URL = "https://" + req.files[0].bucket + ".s3.amazonaws.com/" + req.files[0].key;
										
								
			   
    }

    res.write("Successfully uploaded " + req.files.length + " files!");

    // Use this code to retrieve the value entered in the username field in the index.html
    var username = req.body["name"];
    // Use this code to retrieve the value entered in the email field in the index.html
    var email = req.body["email"];
    // Use this code to retrieve the value entered in the phone field in the index.html
    var phone = req.body["phone"];

    res.write(username + "\n");
    res.write(s3URL + "\n");
    res.write(email + "\n");
    res.write(phone + "\n");

    res.end();
  } catch (err) {
    console.error(err);
    if (!res.headersSent) {
      res.status(500).send("Upload failed.");
    }
  }
}; 

////////////////////////////////////////////////
// Get images for Image Gallery
//
const getImagesFromS3Bucket = async (req, res) => {
  try {
    let imageURL = await listObjects(req, res);
    console.log("ImageURL:", imageURL);
    res.set("Content-Type", "text/html");
    res.write("<div>Welcome to the gallery" + "</div>");
    for (let i = 0; i < imageURL.length; i++) {
      res.write('<div><img src="' + imageURL[i] + '" /></div>');
    }
    res.end();
  } catch (err) {
    console.error(err);
    if (!res.headersSent) {
      res.status(500).send("Could not load gallery.");
    }
  }
};
////////////////////////////////////////////////
// Lookup Database Identifier
//
const getDBIdentifier = async () => {
  const client = new RDSClient({ region: REGION });
  const command = new DescribeDBInstancesCommand({});
  try {
    const results = await client.send(command);
																						   
																								
    return results;
  } catch (err) {
    console.error(err);
    throw err;
  }
};
      
      ////////////////////////////////////////////////
      // Select Record
      //
      const selectRecord = async () => {
        let dbIdentifier = await getDBIdentifier();
        let uname = await getUname();
        let pword = await getPword();
        // let obj = JSON.parse(sec.SecretString);
        try {
          const mysql = require("mysql2/promise");
          // create the connection to database
          const connection = await mysql.createConnection({
            host: dbIdentifier.DBInstances[0].Endpoint.Address,
            user: uname.SecretString,
            password: pword.SecretString,
            database: "company",
          });
      
          // simple query
          const [rows, fields] = await connection.execute("SELECT * FROM `entries`");
          return rows;
        } catch (err) {
          console.error(err);
		throw err;	  
        }
      };
      
      const row = (html) => `<tr>\n${html}</tr>\n`,
        heading = (object) =>
          row(
            Object.keys(object).reduce(
              (html, heading) => html + `<th>${heading}</th>`,
              ""
            )
          ),
        datarow = (object) =>
          row(
            Object.values(object).reduce(
              (html, value) => html + `<td>${value}</td>`,
              ""
            )
          );
      
      function htmlTable(dataList) {
  if (!dataList || dataList.length === 0) {
    return `<table><tr><td>No records found</td></tr></table>`;
  }

  return `<table>
            ${heading(dataList[0])}
										  
            ${dataList.reduce((html, object) => html + datarow(object), "")}
							
						  
          </table>`;
}
       ////////////////////////////////////////////////
      // Select most recent inserted Record ID
      // https://dev.mysql.com/doc/refman/8.4/en/information-functions.html#function_last-insert-id
      //
      const retrieveLastDBRecord = async (req, res) => {
        let dbIdentifier = await getDBIdentifier();
        let uname = await getUname();
        let pword = await getPword();
        try {
          const mysql = require("mysql2/promise");
          // create the connection to database
          const connection = await mysql.createConnection({
            host: dbIdentifier.DBInstances[0].Endpoint.Address,
            user: uname.SecretString,
            password: pword.SecretString,
            database: "company",
          });
      
          // simple query       
          //const [rows, fields] = await connection.execute("SELECT LAST_INSERT_ID() AS LASTID from `entries` ");
          const [rows, fields] = await connection.execute("SELECT MAX( ID ) AS ID FROM `entries` ");
          let id = rows[0].ID;
          console.log("SQL results for rows[0].ID: " + id)
          return id;
        } catch (err) {
          console.error(err);
        }
      };
      
      ////////////////////////////////////////////////
      // Select and Print Record
      //
      const selectAndPrintRecord = async (req, res) => {
        let dbIdentifier = await getDBIdentifier();
        let uname = await getUname();
        let pword = await getPword();
        try {
          const mysql = require("mysql2/promise");
          // create the connection to database
          const connection = await mysql.createConnection({
            host: dbIdentifier.DBInstances[0].Endpoint.Address,
            user: uname.SecretString,
            password: pword.SecretString,
            database: "company",
          });
      
          // simple query
          const [rows, fields] = await connection.execute("SELECT * FROM `entries`");
          res.set("Content-Type", "text/html");
          res.write("Here are the records: " + "\n");
          res.write(htmlTable(rows));
          res.end();
          return rows;
        } catch (err) {
          console.error(err);
    if (!res.headersSent) {
      res.status(500).send("Could not load database records.");
    };
					   
  }
 };
      
      ////////////////////////////////////////////////
      //Insert Record
      //
      const insertRecord = async (req, res) => {
        let dbIdentifier = await getDBIdentifier();
        let uname = await getUname();
        let pword = await getPword();
        try {
		  // console.error("Secret1:", obj.password);
          // console.error("Secret2:", obj.username);						 													 
          // console.error("dbIdentifier:", dbIdentifier.DBInstances[0].Endpoint.Address);
          const mysql = require("mysql2/promise");
          // create the connection to database
          const connection = await mysql.createConnection({
            host: dbIdentifier.DBInstances[0].Endpoint.Address,
            user: uname.SecretString,
            password: pword.SecretString,
            database: "company",
          });
      
          // simple query
let email = req.body["email"];
    let recordNumber = uuidv4();
    let username = req.body["name"];
    let phone = req.body["phone"];

    let s3URL = req.files[0].location;
    if (!s3URL) {
      s3URL = "https://" + req.files[0].bucket + ".s3.amazonaws.com/" + req.files[0].key;
											
								
					
    }

    let statement =
      'INSERT INTO entries(RecordNumber,CustomerName,Email,Phone,Stat,RAWS3URL) VALUES("' +
      recordNumber +
      '","' +
      username +
      '","' +
      email +
      '","' +
      phone +
      '",1,"' +
      s3URL +
      '");';

    const [rows, fields] = await connection.execute(statement);
									
    return rows.insertId;
  } catch (err) {
    console.error(err);
    throw err;
  }
};

//////////////////////////////////
// https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/client/secrets-manager/command/GetSecretValueCommand/
// Directly retrieve the secret value
// GetSecretValueCommand
//

const getUname = async () => {
  
  //console.log("Secret ARN: ",secretARN.SecretList[0].ARN);
  const params = {
    SecretId: "uname",
  };
  const client = new SecretsManagerClient({ region: REGION });
  const command = new GetSecretValueCommand(params);
  try {
    const results = await client.send(command);
    //console.log(results);
    return results;
  } catch (err) {
    console.error(err);
	throw err;		  
  }
};

//////////////////////////////////
// https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/client/secrets-manager/command/GetSecretValueCommand/
// Directly retrieve the secret value
// GetSecretValueCommand
//

const getPword = async () => {
  
  //console.log("Secret ARN: ",secretARN.SecretList[0].ARN);
  const params = {
    SecretId: "pword",
  };
  const client = new SecretsManagerClient({ region: REGION });
  const command = new GetSecretValueCommand(params);
  try {
    const results = await client.send(command);
    //console.log(results);
    return results;
  } catch (err) {
    console.error(err);
	throw err;		  
  }
};

/////////////////////////////////////////////////
// add list SNS topics here
//

const getListOfSnsTopics = async () => {
  const client = new SNSClient({ region: REGION });
  const command = new ListTopicsCommand({});
  try {
    const results = await client.send(command);
    //console.error("Get SNS Topic Results: ", results.Topics.length);
    //console.error("ARN: ", results.Topics[0].TopicArn);
    //return results.Topics[0];
    return results;
  } catch (err) {
    console.error(err);
	throw err;		  
  }
};

///////////////////////////////////////////
// List of properties of Topic ARN
//
const getSnsTopicArn = async () => {
  let snsTopicArn = await getListOfSnsTopics();
  //	console.log(snsTopicArn.Topics[0].TopicArn);
  const params = {
    TopicArn: snsTopicArn.Topics[0].TopicArn,
  };
  const client = new SNSClient({ region: REGION });
  const command = new GetTopicAttributesCommand(params);
  try {
    const results = await client.send(command);
    //console.log("Get SNS Topic Properties results: ",results);
    return results;
  } catch (err) {
    console.error(err);
	throw err;		  
  }
};

///////////////////////////////////////////////////
// Register email with Topic
//
const subscribeEmailToSNSTopic = async () => {
  let topicArn = await getListOfSnsTopics();
  const params = {
    // CHANGE ENDPOINT EMAIL TO YOUR OWN
    Endpoint: "jparraga@illinoistech.edu",
    Protocol: "email",
    TopicArn: topicArn.Topics[0].TopicArn,
  };
  const client = new SNSClient({ region: REGION });
  const command = new SubscribeCommand(params);
  try {
    const results = await client.send(command);
    console.log("Subscribe Results: ", results);
    return results;
  } catch (err) {
    console.error(err);
	throw err;		  
  }
};

///////////////////////////////////////////////
// send message to topic and all subscribers
//
const sendMessageViaEmail = async (req, res) => {
  let publishMessage = await listObjects(req, res);
  const fname = req.files[0].originalname;
  console.log("File uploaded:", fname);
  console.log("URLs collected:", publishMessage);
  var s3URL = "URL not generated due to technical issue.";
  for (let i = 0; i < publishMessage.length; i++) {
    if (publishMessage[i].endsWith(fname)) {
      s3URL = publishMessage[i];
      break;
    }
  }
  let snsTopicArn = await getListOfSnsTopics();
  const params = {
    Subject: "Your image is ready!",
    Message: s3URL,
    TopicArn: snsTopicArn.Topics[0].TopicArn,
  };
  const client = new SNSClient({ region: REGION });
  const command = new PublishCommand(params);
  try {
    const results = await client.send(command);
    //console.log("Send message results: ", results);
    return results;
  } catch (err) {
    console.error(err);
    throw err;			  
  }
};

////////////////////////////////////////////////////////////////////////////////
// https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/client/sqs/command/ListQueuesCommand/

const listSqsQueueURL = async (req, res) => {
  const client = new SQSClient({ region: REGION });
  const input = {};
  const command = new ListQueuesCommand(input);
  try {
    const response = await client.send(command);
    console.log(response["QueueUrls"][0]);
    return response["QueueUrls"][0];
  } catch (err) {
    console.error(err);
    throw err;
  }
};

////////////////////////////////////////////////////////////////////////////////
// https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/client/sqs/command/SendMessageCommand/
// get Send Messages
const sendMessageToQueue = async (recordID) => {
  console.log("Enter Send Message...");
  let sqsQueueURL = await listSqsQueueURL();
													
  const client = new SQSClient({ region: REGION });
  const input = {
    QueueUrl: sqsQueueURL,
    MessageBody: String(recordID),
  };
  const command = new SendMessageCommand(input);

  try {
    const response = await client.send(command);
    return response;
  } catch (err) {
    console.error(err);
    throw err;
  }

};

////////////////////////////////////////////////////////////////////////////////
// Request to index.html or / express will match this route and render this page
//

app.get("/", function (req, res) {
        res.sendFile(__dirname + "/index.html");
      });
      
app.get("/gallery", async function (req, res) {
  await getImagesFromS3Bucket(req, res);
});

app.get("/db", async function (req, res) {
													 
  await selectAndPrintRecord(req, res);
});;
      
app.post("/upload", upload.array("uploadFile", 1), async function (req, res, next) {
  try {
    const insertedID = await insertRecord(req, res);
    await sendMessageToQueue(insertedID);
    await getPostedData(req, res);
  } catch (err) {
    console.error(err);
    if (!res.headersSent) {
      res.status(500).send("Upload failed.");
    }
  }   
      });
      
app.get("/ip", function (req, res) {
  res.end(req.ip);
});

      app.listen(3000, function () {
        console.log("Amazon s3 file upload app listening on port 3000");
      });
      