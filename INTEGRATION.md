In order to work integrated with sharesfor, your application should provide the following:
- a POST requests to sharesfor: https://<your s4s4 url>/routing_form with the following parameters:
    - "userid": the unique ID of the user in your application (Note: sharesfor does not provide user management and the whole user information should be handled and provided by your application)
    - "username": the displayed username 
    - "email": the email address of the user
    - "otype": object type like account, contact, project, etc.
    - "oid": the unique identifier of this object provided by your application
    - "client_id": the client ID of your application defined in sharesfor db for application authorization
    - "api_key": the api key define in sharesfor db for your application.
- An API providing the following routes (the routes are defined during API authorization, see below):
    - api_urls["object_list"]:
            - call type: POST
            - parameters:
                - inp: The string that partially matches with the name of the object, in order to retrieve the matching objects
                - user: user_id, to retrieve only the objects that the user is authorized
            - returns a list of objects in the following json format
                - [{id: {id: [<object type>, <object. id>], name: object name}, name: <display name>}
    - api_urls["object_name"]:
        - parameters
            - otype: object type
            - oid: object id
        - returns object name in string format
    - api_urls["authorized_users"]:
        - parameters
            - otype: object type
            - oid: object id
        - returns a list of users in the following JSON format
            - [{id: <user id>, name: <user name>, email: <user email>}, ... ]

API authorization

The following document should be -manually- added to the authorized_apps document in the sharesfor database:
{
  "client_id": <your application client ID<,
  "api_key": <API password>,
  "api_urls": {
    "object_list": "http://localhost:5015/interfaces/object_list",
    "object_name": "http://localhost:5015/interfaces/object_name",
    "authorized_users": "http://localhost:5015/interfaces/authorized_users"
  }
}
