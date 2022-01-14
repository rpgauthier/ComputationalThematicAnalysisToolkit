#TODO program needs to be adjusted allow french localization
class Common:
    #Common text used everywhere
    WARNING = "Warning"
    ERROR = "Error"
    INFORMATION = "Information"                           
    UNKNOWN = "Unknown"
    DETAILS = "Details"

    CONFIRM_REQUEST = "Please Confirm"
    INPUT_REQUEST = "Please provide Input"

    STARTING = "Starting"
    FINISHED = "Finished"
    CANCELED = "Operation Cancelled"

    OK = "OK"
    SKIP = "Skip"
    PROCEED = "Proceed"
    CANCEL = "Cancel"
    LOAD_ANYWAYS = "Load Anyways"
    PROCEED_ANYWAYS = "Proceed Anyways"

    ADD = "Add"
    SELECT = "Select"
    REMOVE = "Remove"
    INCLUDE = "Include"
    READD = "Readd"

    CREATE = "Create"
    MODIFY = "Modify"
    DELETE = "Delete"
    ACTIONS = "Actions"
    VIEW = "View"

    DELETE_CONFIRMATION = " will be deleted. Are you sure you want to proceed?"

    CHANGE_COLOUR = "Change Colour"

    COPY = "Copy"
    CUT = "Cut"
    PASTE = "Paste"

    UNDO = "Undo"
    REDO = "Redo"

    BOLD = "Bold"
    ITALIC = "Italic"
    UNDERLINE = "Underline"
    STRIKETHROUGH = "Strikethrough"
    FONT = "Font"
    INCREASE_FONT_SIZE = "Increase Font Size"
    DECREASE_FONT_SIZE = "Decrease Font Size"

    NAME = "Name"
    FILENAME = "Filename"
    CREATED_ON = "Created On"

    GROUP = "Group"
    UNGROUP = "Ungroup"

    MERGE = "Merge"
    UNMERGE = "Unmerge"

    ENABLE = "Enable"
    
    SOURCE = "Source"
    TYPE = "Type"
    DATASET = "Dataset"
    FIELD = "Field"
    DOCUMENT = "Document"
    SAMPLE = "Sample"
    MERGED_PART = "Merged Part"
    PART = "Part"
    MERGED_TOPIC = "Merged Topic"
    TOPIC = "Topic"
    CODE = "Code"
    THEME = "Theme"

    USEFULNESS_LABEL = "Usefulness"
    NOT_SURE = "Not Sure"
    NOT_SURE_HELP = "Flags selected entries usefulness as not sure"
    USEFUL = "Useful"
    USEFUL_HELP = "Flags selected entries usefulness as useful"
    NOT_USEFUL = "Not Useful"
    NOT_USEFUL_HELP = "Flags selected entries usefulness as not useful"

    SEARCH = "Search"
    SEARCH_RESULTS_LABEL = " Results"
    SHOW = "Show"
    GOTO = "Go to"
    PAGE = "Page"
    OF = "of"

    ID = "ID"
    WEBSITE = "Website"
    NOTES = "Notes"
    CODES = "Codes"
    THEMES = "Themes"
    NUMBER_OF_CODES = "# of Codes"

    SIZE_WARNING_MSG = "WARNING: may take some time for large datasets"
    TOTAL_TIME_LABEL = "Total Time:"
    CURRENT_STEP_LABEL = "Current Step: "
    CURRENT_STEP_TIME_LABEL = "Current Step Time:"

    MULTIPROCESSING_WARNING_MSG = "A cpu intensive operation is currently in progress."\
                                  "\n Please try current action again after this operation has completed"
    MULTIPROCESSING_CLOSING_MSG = "A cpu intensive operation is currently in progress."\
                                  "\n Are you sure you want to exit the application?"
    
    CONSUMER_KEY = "Consumer Key"
    CONSUMER_SECRET = "Consumer Secret"

class Main(Common):
    APP_NAME = "Computational Thematic Analysis Toolkit"
    NEW_WORKSPACE_NAME = "New_Workspace"

    NEW_WARNING = "You have unsaved changes."\
                  "\nAre you sure you want to creating a new workspace?"\
                  "\nAny unsaved changes will be lost."
    NO_AUTOSAVE_ERROR = "There is no autosave in the app directory."\
                        "\nIf you recently upgraded there may be a save file you can import using the normal load."
    LOAD_WARNING = "You have unsaved changes."\
                   "\nAre you sure you want to load a different workspace?" \
                   "\nAny unsaved changes will be lost."
    LOAD_REQUEST = "Please Choose Workspace to Load"
    
    LOAD_OPEN_FAILURE = "Cannot open workspace "
    LOAD_VERSION_FAILURE1 = "Workspace was created for toolkit version "
    LOAD_VERSION_FAILURE2 = "To load the toolkit needs to be updated"
    LOAD_CANCELED = "Load has been canceled"

    SAVE_AS_REQUEST = "Please Choose Name for Workspace being Saved"
    SAVE_AS_FAILURE = "Failed to save workspace "
    SAVE_FAILURE = "Failed to save workspace "
    CLOSE_WARNING = "Would you like to save your changes before closing?" \
                   "\nIf skipped any recent changes will be lost."

    NEW_BUSY_LABEL = "Creating New Workspace"
    NEW_BUSY_MSG = "Please Wait while new workspace is created.\n"
    NEW_BUSY_STEP = "Creating New Workspace"

    LOAD_BUSY_LABEL = "Loading Workspace"
    LOAD_BUSY_MSG = "Please Wait while data is loaded.\n"
    LOAD_BUSY_MSG_FILE_STEP = "Loading File: "
    LOAD_BUSY_MSG_DATASET_MSG = "- loaded Dataset: "
    LOAD_BUSY_MSG_SAMPLE_MSG = "- loaded Sample: "
    LOAD_BUSY_MSG_CODES_MSG = "- loading Codes"
    LOAD_BUSY_MSG_THEMES_MSG = "- loading Themes"
    LOAD_BUSY_MSG_CONFIG_MSG = "- loading Configurations"
    LOAD_BUSY_MSG_MEMORY_STEP = "Loading Memory"

    SAVE_BUSY_LABEL = "Saving Workspace"
    SAVE_BUSY_MSG = "Please wait while data is saved.\n"
    SAVE_BUSY_MSG_STEP = "Saving File: "
    SAVE_BUSY_MSG_NOTES = "- saving Notes to text."
    SAVE_BUSY_MSG_CONFIG = "- saving Configurations"
    SAVE_BUSY_MSG_DATASETS = "- saving Dataset: "
    SAVE_BUSY_MSG_SAMPLES = "- saving Sample: "
    SAVE_BUSY_MSG_CODES = "- saving Codes"
    SAVE_BUSY_MSG_THEMES = "- saving Themes"
    SAVE_BUSY_MSG_COMPRESSING = "- writing Saved Data"

    AUTO_SAVE_BUSY_STEP = "Autosaving Workspace"

    UPGRADE_BUSY_MSG_WORKSPACE_STEP1 = "Upgrading Workspace version from  "
    UPGRADE_BUSY_MSG_WORKSPACE_STEP2 = " to "
    UPGRADE_BUSY_MSG_DATASETS_MSG = "- upgrading Datasets"
    UPGRADE_BUSY_MSG_DATABASE_MSG = "- upgrading Database"
    UPGRADE_BUSY_MSG_DATABASE_CREATE_MSG = "- converting Workspace to Use Database"
    UPGRADE_BUSY_MSG_SAMPLES_MSG = "- upgrading Samples"
    UPGRADE_BUSY_MSG_CODES_MSG = "- upgrading Codes"
    UPGRADE_BUSY_MSG_THEMES_MSG = "- upgrading Themes"

    SHUTDOWN_BUSY_LABEL = "Shutting Down Application"
    SHUTDOWN_BUSY_POOL_MSG = "- shutting down Process Pool"
    
    NAME_MISSING_ERROR = "Please enter a Name."
    FILENAME_MISSING_ERROR = "Please enter a Filename"
    
    OF_AN_ESTIMATED_LABEL = "of an estimated "
    COMPLETED_IN_LABEL = "- completed in "

    #Menu related text
    SHOW_HIDE = "Show/Hide "
    #File Menu
    FILE_MENU = "File"
    OPTIONS = "Options"
    NEW = "New"
    NEW_TOOLTIP = "Create a New Workspace"
    RESUME = "Resume"
    RESUME_TOOLTIP = "Resume the last autosaved workspace"
    LOAD = "Load"
    LOAD_TOOLTIP = "Load an Existing Workspace"
    SAVE = "Save"
    SAVE_TOOLTIP = "Save Current Workspace"
    SAVE_AS = "Save As"
    SAVE_AS_TOOLTIP = "Save the Current Workspace with a new name"
    IMPORT_CODEBOOK = "Import REFI-QDA Codebook"
    IMPORT_CODEBOOK_TOOLTIP = "Import Codes from file that follows the REFI-QDA Codebook specifications"
    EXPORT_CODEBOOK = "Export REFI-QDA Codebook"
    EXPORT_CODEBOOK_TOOLTIP = "Export Codes and Themes to a file that follows the REFI-QDA Codebook specifications"
    EXPORT_PROJECT = "Export REFI-QDA Project"
    EXPORT_PROJECT_TOOLTIP = "Export Workspace into a file that follows the REFI-QDA Project specifications"
    EXIT = "Exit"
    EXIT_TOOLTIP = "Exit Application"
    #Help Menu
    HELP_MENU = "Help"
    ABOUT = "About"

    #Options Dialog
    OPTIONS_LABEL = OPTIONS
    OPTIONS_ADVANCED_MODES_LABEL = "Advanced Modes"
    OPTIONS_MULTIPLEDATASETS_LABEL = "Allow Multiple Datasets Mode (not yet fully tested)"
    OPTIONS_ADJUSTABLE_LABEL_FIELDS_LABEL = "Allow adjusting label fields during retrieval"
    OPTIONS_ADJUSTABLE_COMPUTATIONAL_FIELDS_LABEL = "Allow adjusting computational fields during retrieval"
    CONSUMER_KEY_MISSING_ERROR = "You need to enter a Consumer Key."
    CONSUMER_SECRET_MISSING_ERROR = "You need to enter a Consumer Secret."
    INVALID_CREDENTIALS_ERROR = "Invalid credentials."
    INSUFFICIENT_CREDENTIALS_ERROR = "Your credentials do not allow access to this resource."

    #Import Codebook Dialogs
    IMPORT_CODEBOOK_LABEL = IMPORT_CODEBOOK
    IMPORT_CODEBOOK_INFO = "When importing a REFI-QDA Codebook the following mappings will occur:"\
                           "\n1) Codes will become Codes"\
                           "\n1a) Any Codes' Descriptions will become Notes"\
                           "\n2) Sets will become Themes"\
                           "\n1a) Any Sets' Descriptions will become Theme Notes"\
                           "\n2a) Any Sets' MemberCodes will become Theme to Code References"
    IMPORT_CODEBOOK_CONFIRMATION_REQUEST = "Please confirm you wish to import an external codebook file into this project."\
                                           "\nWARNING: Existing codes may be updated if they had previously been exported or imported and are present in the external codebook"
    IMPORT_CODEBOOK_SUCCESS = "Codes and Themes were successfully imported from an REFI-QDA Codebook."
    IMPORT_CODEBOOK_ERROR_IO = "Cannot load specified codebook file.\nPlease check that you have read access to the file and directory."
    IMPORT_CODEBOOK_ERROR_XML = "XML Error occured when importing codebook file."
    
    #Export Codebook Dialogs
    EXPORT_CODEBOOK_LABEL = EXPORT_CODEBOOK
    EXPORT_CODEBOOK_INFO = "When creating a REFI-QDA Codebook the following mappings will occur:"\
                           "\1) Codes will becoming Codes"\
                           "\n1a) Quotations will not be included"\
                           "\n1b) Any Code notes will become Descriptions"\
                           "\n2) Themes will become Sets"\
                           "\n2a) All Themes will lose hierarchy information and be treated as independent"\
                           "\n2b) Quotations will not be included"\
                           "\n2c) Any Theme notes will become Descriptions"\
                           "\n2d) Any Theme to Code References will become Sets' MemberCodes"
    EXPORT_CODEBOOK_SUCCESS = "Codes and Themes were successfully exported as an REFI-QDA Codebook."
    EXPORT_CODES_ERROR_NO_DATA = "Workspace has no codes to export as a Codebook.\nIf exporting themes please create atleast one temporary code."
    EXPORT_CODEBOOK_ERROR_XML = "XML Error occured when checking created codebook."
    EXPORT_CODEBOOK_ERROR_IO = "Cannot save specified codebook file.\nPlease check that you have write access to directory and if replacing a file it is not locked."
    
    #Export Project Dialog
    EXPORT_PROJECT_LABEL = EXPORT_PROJECT
    EXPORT_PROJECT_INFO = "When creating a REFI-QDA Project the following mappings will occur:"\
                          "\n1) Any tab notes will not be included"\
                          "\n2) Datasets will becoming Cases"\
                          "\n2a) Unselected data will not be included"\
                          "\n2b) Dataset Details will become a Description"\
                          "\n3) Samples will become Cases"\
                          "\n3a) Unselected data will not be included"\
                          "\n3b) Sample Details will become a Description"\
                          "\n4) Selected Documents will become TextSources"\
                          "\n4a) Any Document content will become a plain text file"\
                          "\n4b) Any Document notes will become Descriptions"\
                          "\n5) Codes will becoming Codes"\
                          "\n5a) Quotations will not be included"\
                          "\n5b) Any Code notes will become Descriptions"\
                          "\n5c) Selected Documents of a code will become PlainTextSelections that cover the full Documents"\
                          "\n5d) Selected Lines of Documents of a code will become PlainTextSelections that cover the selected text"\
                          "\n6) Themes will become Sets"\
                          "\n6a) All Themes will lose hierarchy information and be treated as independent"\
                          "\n6b) Quotations will not be included"\
                          "\n6c) Any Theme notes will become Descriptions"\
                          "\n6d) Code References will become MemberCodes"
    EXPORT_PROJECT_SUCCESS = "Workspace was successfully exported as an REFI-QDA Project."
    EXPORT_PROJECT_ERROR_NO_DATA = "Workspace has no data to export as a Project."
    EXPORT_PROJECT_ERROR_XML = "XML Error Occured when checking created project."
    EXPORT_PROJECT_ERROR_IO = "Cannot save specified project file.\nPlease check that you have write access to directory and if replacing a file it is not locked."

    #About dialog labels
    ABOUT_LABEL = ABOUT
    ABOUT_VERSION_LABEL = "Version: "
    ABOUT_OSF_LABEL = "OSF link"
    ABOUT_OSF_URL = "https://osf.io/b72dm/"
    ABOUT_GITHUB_LABEL = "Github link"
    ABOUT_GITHUB_URL = "https://github.com/rpgauthier/ComputationalThematicAnalysisToolkit"

    #new version dialog labels
    NEW_VERSION_LABEL = "New Version Available"
    CURRENT_VERSION_LABEL = "The toolkit you are using is Version "
    LATEST_VERSION_LABEL = " is avaliable for download."
    APP_INSTRUCTIONS = "To upgrade please perform the following steps:"
    APP_INSTRUCTION1 = "1) Download the approriate installer from "
    LATEST_RELEASE_LABEL = "Latest Release"
    LATEST_RELEASE_URL = "https://github.com/rpgauthier/ComputationalThematicAnalysisToolkit/releases/latest"
    APP_INSTRUCTION2 = "2) Close this application"
    APP_INSTRUCTION3 = "3) Run the downloaded installer"
    WORKSPACE_INSTRUCTIONS = "Once installed any workspace you load will be automatically upgraded."

    #Module Labels
    GENERAL_LABEL = "General"
    COLLECTION_LABEL = "Data Collection"
    FILTERING_LABEL = "Data Cleaning & Filtering"
    FILTERING_MENU_LABEL = "Data Cleaning && Filtering"
    SAMPLING_LABEL = "Modelling & Sampling"
    SAMPLING_MENU_LABEL = "Modelling && Sampling"
    CODING_LABEL = "Coding"
    REVIEWING_LABEL = "Reviewing"
    REPORTING_LABEL = "Reporting"
    NOTES_LABEL = "Notes"
    TWITTER_LABEL = "Twitter"

    MULTIPROCESSING_LABEL = "Multiprocessing Options"
    MAXIMUM_POOL_SIZE_LABEL = "Maximum Pool Size"

class Datasets(Common):
    #common
    DESCRIPTION = "Description"
    DOCUMENT_NUM = "# of Documents"
    RETRIEVED_ON = "Retrieved On"
    IMPORTED_ON = "Imported On"
    PREPARED_ON = "Prepared On"
    LANGUAGE = "Language"
    UTC = "UTC"
    CUSTOMIZE_LABEL_FIELDS = "Customize Label Fields"
    CUSTOMIZE_COMPUTATIONAL_FIELDS = "Customize Computational Fields"
    DATASET_DELETE_TOOLTIP = "Delete this dataset from the workspace"
    REFRESHING_DATASETS_BUSY_STEP = "Refreshing Data for Dataset: "
    
    #Common Dialog
    DATASET_CONFIGURATIONS = "Dataset Configurations"
    NAME_TOOLTIP = "Choose a unique name for the new dataset"
    NAME_EXISTS_ERROR = "Name must be unique"
    TYPE_ERROR = "Please select a Dataset Type"
    DATA_CONSTRAINTS = "Data Constraints"
    START_DATE = "Start Date"
    #START_DATETIME = "Start Date & Time"
    START_DATE_TOOLTIP = "Needs to be less than of equal to End Date"
    END_DATE = "End Date"
    #END_DATETIME = "End Date & Time"
    END_DATE_TOOLTIP = "Needs to be greater than of equal to Start Date"
    DATE_ERROR = "Start Date needs to be before End Date"
    SPECIAL_DATA_FIELDS = "Special Data Fields"
    ETHICAL_CONSIDERATIONS = "Ethical Considerations"
    LABEL_FIELDS = "Label Fields"
    LABEL_FIELDS_TOOLTIP = "Choose additional fields you need to use when identifying and interpreting the data."\
                             "\nIf a field occurs multiple times for the same id, the first occurance will be used."
    COMBINED_LABEL_FIELDS = "Combined Label Fields"
    COMBINED_LABEL_FIELDS_TOOLTIP = "Choose additional fields you need to use when identifying and interpreting the data."\
                                      "\nIf a field occurs multiple times for the same id, it's content's will be concatinated."
    COMPUTATIONAL_FIELDS = "Computational Fields"
    COMPUTATIONAL_FIELDS_TOOLTIP = "Choose fields you want computational methods to use when identifing samples of interest from the data."\
                             "\nIf a field occurs multiple times for the same id, the first occurance will be used."
    COMBINED_COMPUTATIONAL_FIELDS = "Combined Computational Fields"
    COMBINED_COMPUTATIONAL_FIELDS_TOOLTIP = "Choose fields you want machine learning to use when identifing samples of interest from the data."\
                                      "\nIf a field occurs multiple times for the same id, it's content's will be concatinated."
    
    
    #Reddit Specific Dialog
    REDDIT_RETRIEVE_LABEL = "Retrieve New Reddit Dataset"
    REDDIT_RETRIEVED_LABEL = "Retrieved Reddit Dataset Details"
    REDDIT_LABEL = "Reddit"
    REDDIT_SUBREDDIT = "www.reddit.com/r/"
    REDDIT_SUBREDDIT_TOOLTIP = "Exact case-sensitive spelling of the subreddit for retrieval."\
                               "\nIf you require multiple subreddits in the same dataset then seperate the subreddit names by comma."
    REDDIT_SUBREDDIT_MISSING_ERROR = "Please enter a Subreddit."
    REDDIT_SEARCH_BY = "Search by"
    REDDIT_CONTAINS_TEXT = "Contains Text"
    REDDIT_DISCUSSIONS = "Discussions"
    REDDIT_DISCUSSIONS_TOOLTIP = "Will group any Reddit submissions and/or comments retrieved into discussions"
    REDDIT_SUBMISSIONS = "Submissions"
    REDDIT_SUBMISSIONS_TOOLTIP = "Will retrieve any Reddit submissions between the start and end dates"
    REDDIT_COMMENTS = "Comments"
    REDDIT_COMMENTS_TOOLTIP = "Will retrieve any Reddit comments between the start and end dates"
    REDDIT_SUBMISSIONS_NUM = "# of Submissions"
    REDDIT_COMMENTS_NUM = "# of Comments"
    REDDIT_ARCHIVED_TOOLTIP = "Use the local subreddit archive to create the dataset."
    REDDIT_ARCHIVED = "Local Subreddit Archive"
    
    REDDIT_UPDATE_PUSHSHIFT = "Local Subreddit Archive updated using Pushshift.io"
    REDDIT_UPDATE_PUSHSHIFT_TOOLTIP = "For any part of the period between the start and end dates that the local subreddit archive does not have data,"\
                                       "update the archive using pushshift.io API"\
                                       "\nThen use the archive to create the dataset."\
                                       "\nWARNING: This operation may take between several minutes to hours depending on sizze of existing local subreddit archive"
    REDDIT_FULL_PUSHSHIFT = "Full retrieval from Pushshift.io"
    REDDIT_FULL_PUSHSHIFT_TOOLTIP = "Remove any existing local subreddit archive."\
                                    "Then retrieve a new archive from pushshift.io API for the period between the start and end dates."\
                                    "Then use the archive to create the dataset"\
                                    "\nWARNING: This operation is a slow and may take several hours"
    REDDIT_UPDATE_REDDITAPI = "Local Subreddit Archive and updated using Pushshift.io and Reddit API"
    REDDIT_UPDATE_REDDITAPI_TOOLTIP = "For any part of the period between the start and end dates that the local subreddit archive does not have data,"\
                                      "update the archive using pushshift.io API"\
                                      "Then update the local subreddit archive for the period between the start and end dates using the Reddit API."\
                                      "Then use the updated archive to create the dataset"\
                                      "\nWARNING: This operation is slow and may take several hours"
    REDDIT_FULL_REDDITAPI = "Full retrieved from Pushshift.io and updated using Reddit API"
    REDDIT_FULL_REDDITAPI_TOOLTIP = "Remove any existing local subreddit archive."\
                                    "Then retrieve a new archive from pushshift.io API for the period between the start and end dates."\
                                    "Then update the archive for the period between the start and end dates using the Reddit API."\
                                    "Then use the updated archive to create the dataset"\
                                    "\nWARNING: This operation is slow and may take several hours"
    
    #Twitter Specific Dialog
    TWITTER_RETRIEVE_LABEL = "Retrieve New Twitter Dataset"
    TWITTER_RETRIEVED_LABEL = "Retrieved Twitter Dataset Details"
    TWITTER_LABEL = "Twitter"
    CONSUMER_KEY_TOOLTIP = "The API key of a project created in the Twitter Developer portal. Do not include quotes."
    CONSUMER_SECRET_TOOLTIP = "The API secret of a project created in the Twitter Developer portal. Do not include quotes."
    TWITTER_TWEETS = "Tweets"
    TWITTER_TWEETS_NUM = "# of Tweets"
    TWITTER_QUERY = "Query"
    TWITTER_QUERY_HYPERLINK = "https://developer.twitter.com/en/docs/twitter-api/v1/tweets/search/guides/standard-operators"
    TWITTER_QUERY_TOOLTIP = "Query needs to follow these rules: " + TWITTER_QUERY_HYPERLINK
    TWITTER_QUERY_RADIOBUTTON_TOOLTIP = "Use a Twitter query to create the dataset, using these rules: " + TWITTER_QUERY_HYPERLINK
    TWITTER_QUERY_MISSING_ERROR = "You need to enter a query."
    TWITTER_QUERY_PLACEHOLDER = "ex. life OR technology from:google"
    TWITTER_TWEET_ATTRIBUTES = "Tweet Attributes"
    TWITTER_TWEET_ATTRIBUTES_RADIOBUTTON_TOOLTIP = "Use specific tweet attributes to create the dataset."
    TWITTER_KEYWORDS = "Keywords"
    TWITTER_KEYWORDS_PLACEHOLDER = "ex. COVID vaccine, health, safety"
    TWITTER_HASHTAGS = "Hashtags"
    TWITTER_HASHTAGS_PLACEHOLDER = "ex. #toronto, #raptors"
    TWITTER_ACCOUNTS = "Accounts"
    TWITTER_ACCOUNT_PLACEHOLDER = "ex. JustinTrudeau"

    #CSV Specific Dialog
    CSV_RETRIEVE_LABEL = "Retrieve New CSV Dataset"
    CSV_RETRIEVED_LABEL = "Retrieved CSV Dataset Details"
    CSV_LABEL = "CSV"
    CSV_ROWS_NUM = "# of Rows"
    CSV_DATASETFIELD = "Dataset Field"
    CSV_DATASETFIELD_TOOLTIP = "If the csv file contains data from a single source leave this field blank."\
                          "If the csv file contains multiple sources please choose a field differentiates those sources.\n"\
                          "This is important if dealing with multiple languages as different processing may be required."
    CSV_IDFIELD = "Id Field"
    CSV_IDFIELD_TOOLTIP = "Choose a field to use as id to documents.\n"\
                          "If id is unique then every row will be treated as a document.\n"\
                          "If id is not unique, rows with the same id will be merged."
    CSV_IDFIELD_MISSING_ERROR = "Please choose an field to use as an id."
    CSV_IDFIELD_DEFAULT = "<Assign based on Row Number>"
    CSV_URLFIELD = "URL Field"
    CSV_URLFIELD_TOOLTIP = "Choose a field to use as url to link to the online version of the documents."
    CSV_DATETIMEFIELD = "Datetime Field"
    CSV_DATETIMEFIELD_TOOLTIP = "Choose a field to use as datetime to documents."
    CSV_DATETIMETZ_MISSING_ERROR = "Please choose the time zone for the contents of the datatime field"
    
    #Retrieval Streps and Messages
    #Common
    RETRIEVING_LABEL = "Retrieval Inprogress for Dataset: "
    RETRIEVING_BEGINNING_MSG = "Please wait while dataset is retrieved.\n"
    RETRIEVING_DOWNLOADING_ALL_MSG = "- all data for month: "
    RETRIEVING_DOWNLOADING_NEW_MSG = "- new data for month: "
    RETRIEVING_IMPORTING_FILE_MSG = "- importing from file: "
    RETRIEVING_BUSY_CONSTRUCTING_STEP = "Datasets are being constructed."
    RETRIEVAL_FAILED_ERROR = "Retrieval failed for one or more datasets.\nPlease try again later."
    NO_DATA_AVAILABLE_ERROR = "No data retrieved.\nPlease trying again later as requested data may not yet be available."
    #Reddit
    RETRIEVING_REDDIT_REMOVE_SUBREDDIT_ARCHIVE_STEP = "Deleting local archive for subreddit: "
    RETRIEVING_REDDIT_DOWNLOADING_SUBMISSIONS_STEP = "Downloading Submission Data"
    RETRIEVING_REDDIT_DOWNLOADING_COMMENTS_STEP = "Downloading Comment Data"
    RETRIEVAL_REDDIT_FAILED_SUBMISSION = "- failed to retrieve submissions for month "
    RETRIEVAL_REDDIT_FAILED_COMMENT = "- failed to retrieve comments for month "
    RETRIEVING_REDDIT_IMPORTING_SUBMISSION_STEP = "Importing required submission data"
    RETRIEVING_REDDIT_IMPORTING_COMMENT_STEP = "Importing required comment data"
    RETRIEVING_REDDIT_PREPARING_DISCUSSION_STEP = "Preparing Discussion Data for Application use"
    RETRIEVING_REDDIT_PREPARING_SUBMISSION_STEP = "Preparing Submission Data for Application use"
    RETRIEVING_REDDIT_PREPARING_COMMENT_STEP = "Preparing Comment Data for Application use."
    RETRIEVING_REDDIT_SEARCHING_DATA_STEP1 = "Selecting Data that contains ["
    RETRIEVING_REDDIT_SEARCHING_DATA_STEP2 = "] in a text field."
    #Twitter
    RETRIEVING_TWITTER_DOWNLOADING_TWEETS_STEP = "Downloading Twitter tweets data"
    RETRIEVING_TWITTER_IMPORTING_TWEET_STEP = "Importing required Twitter tweets data"
    RETRIEVING_TWITTER_RATE_LIMIT_WARNING = "Twitter API rate limit has been reached. The number of tweets will be shortened."
    RETRIEVING_TWITTER_BUSY_PREPARING_DATA_STEP = "Preparing Twitter Data for Application use."
    #CSV
    RETRIEVING_CSV_IMPORTING_FILE_STEP = "Importing from file: "
    RETRIEVING_CSV_PREPARING_DATA_STEP = "Preparing CSV Data for Application use."
    
    #Tokenizing 
    TOKENIZING_BUSY_STEP = "Tokenizing Data"
    TOKENIZING_BUSY_STARTING_FIELD_MSG = "- Starting to tokenize field: "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG1 = "-- completed tokenizing threads "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG2 = " of "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG3 = " for field: "
    TOKENIZING_BUSY_STEP_TFIDF_STEP = "Calculating TFIDF values"
    TOKENIZING_BUSY_STARTING_TFIDF_MSG = "- Starting to calculate TFIDF values"
    TOKENIZING_BUSY_COMPLETED_TFIDF_MSG = "- Completed to calculating TFIDF values"

    #Changing Name
    CHANGING_NAME_LABEL = "Changing Name"
    CHANGING_NAME_STEP = "Updating Dataset Name"
    CHANGING_NAME_MSG1 = "- changing from: "
    CHANGING_NAME_MSG2 = " to: "

    #Changing Language
    CHANGING_LANGUAGE_BUSY_LABEL = "Changing Language"
    CHANGING_LANGUAGE_STEP = "Updating Dataset Language"

class Samples(Main):
    #Model types
    GENERIC_SECTION_LABEL = "Generic Sampling"
    RANDOM_LABEL = "Random"
    RANDOM_DESC = "This sampling approach depends on the the assumption that codes are uniformly distributed across the data."\
                  "\nHowever, assuming codes follow a uniform distribution may restrict visability of interesting infrequent codes in the data."
    RANDOM_URL = "https://academic.oup.com/fampra/article/13/6/522/496701"
    TOPICMODEL_SECTION_LABEL = "Topic Model Sampling"
    TOPICMODEL_SECTION_DESC = "Topic model sampling attempts to generate samples in the form of groups of documents that are likely to contain similar topics."\
                              "\nThese groups can contain interesting phenomena that can be used to explore the data, develop codes, and review themes."\
                              "\nHowever, generated topic model samples should to be treated as windows that look at potentially interesting parts of the data rather than as a generalizable representation of the data."
    TOPICMODEL_SECTION_LINK = ""
    LDA_LABEL = "Latent Dirchlet Allocation"
    LDA_DESC = "This topic model is suited to identifying topics in long texts, such as discussions, where multiple topics can co-occur"
    LDA_URL = "https://dl.acm.org/doi/10.5555/944919.944937"
    BITERM_LABEL = "Biterm"
    BITERM_DESC = "This topic model is suited to identifying topics in short texts, such as tweets and instant messages"
    BITERM_URL = "https://dl.acm.org/doi/10.1145/2488388.2488514"
    NMF_LABEL = "Non-Negative Matrix Factorization"
    NMF_DESC = "This topic model is suited to rough identifying topics when performing initial explorations"
    NMF_URL = "https://dl.acm.org/doi/book/10.5555/aai28114631"

    #model list columns and tools
    SAMPLE_NAME = "Name"
    SAMPLE_TYPE = "Type"
    GENERATE_TIME = "Time to Generate"
    LDA_TOPICS = "Topics"
    CREATE_RANDOM = "Create " + RANDOM_LABEL
    CREATE_RANDOM_TOOLTIP = "Create a new Random Model of a dataset"
    CREATE_LDA = "Create " + LDA_LABEL
    CREATE_LDA_TOOLTIP = "Create a new Latent Dirchlet Allocation Topic Model of a dataset"
    CREATE_BITERM = "Create " + BITERM_LABEL
    CREATE_BITERM_TOOLTIP = "Create a new Biterm Topic Model of a dataset"
    CREATE_NMF = "Create " + NMF_LABEL
    CREATE_NMF_TOOLTIP = "Create a new Non-Negative Matrix Factorization Topic Model of a dataset"
    
    DELETE_SAMPLE_LABEL = "Delete Sample"
    DELETE_SAMPLE_WARNING = "\nWARNING this action cannot be undone."

    MERGE_TOPIC_LABEL = "Merge Topics"
    MERGE_TOPIC_SHORTHELP = "Create a new Merged Topic from selected Topics"
    SPLIT_TOPIC_LABEL = "Split Topics"
    SPLIT_TOPIC_SHORTHELP = "Remove selected topics from their Merged Topic"
    REMOVE_TOPIC_LABEL = "Remove Topics"
    REMOVE_TOPIC_SHORTHELP = "Remove selected topics from the model"
    REMOVE_TOPIC_WARNING = "\nWARNING this action cannot be undone."
    PROBABILITY_CUTOFF_LABEL = "Probability Cutoff "
    PROBABILITY_CUTOFF_TOOLTIP = "Include documents in a topic when the model predicts the probability of the topic being present in the document is greater or equal to the cutoff"

    RESTORE_RULES = "Restore Rules"
    RESTORE_RULES_TOOLTIP = "Restores the rules of the dataset back to the version used when this sample was generated."
    CONFIRM_RESTORE_RULES = "Are you sure that you want to replace all existing filter rules with the rules used when generating this sample."
    RESTORE_COMPUTATIONAL_FIELDS = "Restore Computational Fields"
    RESTORE_COMPUTATIONAL_FIELDS_TOOLTIP = "Restores the computational fields of the dataset back to the version used when this sample was generated."
    CONFIRM_RESTORE_COMPUTATIONAL_FIELDS = "Are you sure that you want to replace all existing computational fields of the dataset with the fields used when generating this sample."
    RESTORE_BEGINNING_MSG = "Beginning Restore"
    RESTORE_REPLACINGRULES_MSG = "Replacing Rules"
    RESTORE_REPLACINGFIELDS_MSG = "Replacing Computational Fields"
    RESTORE_COMPLETED_MSG = "Restore Completed"



    #random model panel

    #lda model panel
    TOPIC_LISTS = "Topic Lists"
    TOPIC_NUM = "Topic #"
    WORDS = "Words"
    LABEL = "Label"
    WORDS_PER_TOPIC1 = "Top"
    WORDS_PER_TOPIC2 = "Words of each Topic"

    #Sample
    SAMPLE_REQUEST = "Choose number of enteries to sample:"

    NOT_SAVED_WARNING = "You need to save the workspace to generate an LDA Model"
    CURRENTLY_GENERATING = "Currently Generating Model"
    INPROGRESS = "Inprogress"
    CHECK_STATUS = "Check Status"
    CHECK_STATUS_TOOLTIP = "Check if Model is Ready"

    NUMBER_OF_TOPICS_CHOICE = "Choose Number of Topics"
    NUMBER_OF_TOPICS_TOOLTIP = "Modelling more topics takes longer but may help identify less common topics"
    NUMBER_OF_TOPICS = "Number of Topics"
    NUMBER_OF_PASSES_CHOICE = "Choose Number of Passes"
    NUMBER_OF_PASSES_TOOLTIP = "More passes causes modelling to take longer but may help produce more cohesive topics"
    NUMBER_OF_PASSES = "Number of Passes"
    NUMBER_OF_DOCUMENTS = "Number of Documents"
    DATASET = Datasets.DATASET
    DATASET_MISSING_ERROR = "Dataset was not chosen." \
                            "\nPlease choose a dataset for the model."
    DATASET_NOTAVAILABLE_ERROR = "No Data is available." \
                            "\nPlease load data into the project before trying to create a model."
    TYPE_UNKNOWN_ERROR = "Failed to create sample due to unknown type."
    AFTERFILTERING_LABEL1 = "After filtering "
    AFTERFILTERING_LABEL2 = " documents remained of the "
    AFTERFILTERING_LABEL3 = " documents available"
    

    GENERATE_WARNING = "\nWARNING: Do not shut down program or else model will not be created."
    GENERATE_NOTSAVED_WARNING = "Workspace has not yet been saved."\
                                "\nTo generate this type of sample you need to save the workspace"
    GENERATING_DEFAULT_LABEL = "Generating Sample"
    GENERATING_DEFAULT_MSG = "Begining Generation."
    GENERATING_PREPARING_MSG = "Datasets are being prepared"
    GENERATING_RANDOM_SUBLABEL = "Creating Random Sample: "
    GENERATING_CUSTOM_SUBLABEL = "Creating Custom Sample: "
    GENERATING_LDA_SUBLABEL = "Creating LDA Topic Sample: "
    GENERATING_LDA_MSG2 = "Initalizing LDA Topic Model"
    GENERATING_LDA_MSG3 = "Generating LDA Topic Model"
    GENERATING_BITERM_SUBLABEL = "Creating Biterm Topic Sample: "
    GENERATING_BITERM_MSG2 = "Initalizing Biterm Topic Model"
    GENERATING_BITERM_MSG3 = "Generating Biterm Topic Model"    
    GENERATING_NMF_SUBLABEL = "Creating NMF Topic Sample: "
    GENERATING_NMF_MSG2 = "Initalizing NMF Topic Model"
    GENERATING_NMF_MSG3 = "Generating NMF Topic Model"

    GENERATED_DEFAULT_LABEL = "Generated Sample"
    GENERATED_LDA_SUBLABEL = "Loading results for LDA Topic Sample: "
    GENERATED_LDA_COMPLETED_PART1 = "LDA Topic Model Generation will continue running in background."\
                                    +"\nA new dialog will open when completed."
    GENERATED_BITERM_SUBLABEL = "Loading results for Biterm Topic Sample: "
    GENERATED_BITERM_COMPLETED_PART1 = "Biterm Topic Model Generation will continue running in background."\
                                    +"\nA new dialog will open when completed."
    GENERATED_NMF_COMPLETED_PART1 = "NMF Topic Model Generation will continue running in background."\
                                    +"\nA new dialog will open when completed."

    #review list table column labels
    REVIEW_NAME = "Review Name"
    DATASET_NAME = "Dataset Name"
    REVIEW_TYPE = "Type"
    SAMPLE_NUM = "# of Samples"

class Collection(Main, Datasets):
    ETHICS_CONFIRMATION = "I have considered "
    ETHICS_CONFIRMATION_MISSING_ERROR = "Before proceeding please confirm that you have taken time to consider "
    ETHICS_COMMUNITY1_REDDIT = "the subreddit's guidelines, rules, and terms of use."
    ETHICS_COMMUNITY1 = "the online community's guidelines, rules, and terms of use."
    ETHICS_COMMUNITY2_REDDIT = "the impact of our project on the subreddit's community."
    ETHICS_COMMUNITY2 = "the impact of our project on the online community."
    ETHICS_RESEARCH = "the research community's ethical guidelines and rules on online public data collection."
    ETHICS_INSTITUTION = "our institution's ethical guidelines and rules on online public data collection."
    ETHICS_REDDIT = "Reddit's policies and terms of use for collecting data."
    ETHICS_REDDIT_URL = "https://www.redditinc.com/policies/"
    ETHICS_REDDITAPI_URL = "https://www.reddit.com/wiki/api-terms"
    ETHICS_PUSHSHIFT = "that this toolkit uses the Pushshift.io api to collect Reddit Data."

    INCLUDE_RETWEETS = "Include retweets"
    RETRIEVAL_NOTICE_TWITTER = "* Currently, only (English) tweets up to 7 days back from the current date may be retrieved. *"
    ETHICS_TWITTER = "and agree to Twitter's developer agreement and policy."
    ETHICS_TWITTER_URL = "https://developer.twitter.com/en/developer-terms/agreement-and-policy"

    ONLINE_SOURCES = "Online Sources"
    REDDIT_DESC = "Online communities' public discussions (made up of submissions and comments)."
    REDDIT_URL = "https://www.reddit.com/"
    TWITTER_DESC = "Online public comments."
    TWITTER_URL = "https://twitter.com/"
    LOCAL_SOURCES = "Local Sources"
    CSV_DESC = "Used to import datasets created outside of this toolkit. The csv file must be encoded using utf-8."


    DATASETSLIST_LABEL = "Datasets List"
    DATASETS_RETRIEVE_LABEL = "Retrieve"
    DATASETS_RETRIEVE_TOOLTIP = "Retrieve new datasets for workspace"
    DATASETS_RETRIEVE_REDDIT = "Retrieve " + Datasets.REDDIT_LABEL
    DATASETS_RETRIEVE_REDDIT_TOOLTIP = "Retrieve new Reddit datasets for workspace"
    DATASETS_RETRIEVE_TWITTER = "Retrieve " + Datasets.TWITTER_LABEL
    DATASETS_RETRIEVE_TWITTER_TOOLTIP = "Retrieve new Twitter datasets for workspace"
    DATASETS_IMPORT_CSV = "Import " + Datasets.CSV_LABEL
    DATASETS_IMPORT_CSV_TOOLTIP = "Import a CSV dataset into workspace"
    DATASETS_GROUP_TOOLTIP = "Selected datasets will be grouped"
    DATASETS_GROUP_NAME = "Group Name:"
    DATASETS_UNGROUP_TOOLTIP = "Selected datasets will be ungrouped"
    DATASETS_DELETE_DATASET = "Delete Dataset"
    DATASETS_DELETE_TOOLTIP = "Selected datasets will be removed"
    DATASETS_DELETE_CONFIRMATION_WARNING = "\nWARNING this action can only be undone by adding new datasets."

    DATASETSDATA_LABEL = "Dataset Data"
    VIEW_DETAILS = "View Details"
    CUSTOMIZE_FIELDS = "Customize Fields"

    FIELDS_LABEL = "Fields"
    FIELDS_AVAILABLE_LABEL = "Available Fields"
    FIELDS_INCLUDED_LABEL = 'Included Fields'
    FIELDS_ADD_TOOLTIP = "Selected fields will be added to "
    FIELDS_REMOVE_TOOLTIP = "Selected fields will be removed from "
    FIELDS_EXISTS_ERROR = "You have already included the field: "

    DELETING_BUSY_LABEL = "Deleting Datasets"
    DELETING_BUSY_PREPARING_MSG = "Preparing to Delete Selected Datasets"
    DELETING_BUSY_REMOVING_MSG = "- Deleting Dataset: "

    ADDING_COMPUTATIONAL_FIELDS_BUSY_LABEL = "Adding Computational Fields"
    ADDING_LABEL_FIELDS_BUSY_LABEL = "Adding Label Fields"
    ADDING_FIELDS_BUSY_PREPARING_MSG = "Preparing to Add Selected Fields"
    ADDING_FIELDS_BUSY_LABEL = "Adding Fields"
    ADDING_FIELDS_BUSY_MSG = "- Adding Selection: "

    REMOVING_COMPUTATIONAL_FIELDS_BUSY_LABEL = "Removing Computational Fields"
    REMOVING_LABEL_FIELDS_BUSY_LABEL = "Removing Label Fields"
    REMOVING_FIELDS_BUSY_PREPARING_MSG = "Preparing to Remove Selected Fields"
    REMOVING_FIELDS_BUSY_LABEL = "Removing Fields"
    REMOVING_FIELDS_BUSY_MSG = "- Removing Selection: "

    UPDATING_DATASET_BUSY_MSG = "Updating Data Collection's Dataset Panel"

    LOAD_BUSY_MSG_CONFIG = "Loading Data Collection Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Data Collection Configurations"

#depends on Datasets, Main, and Common
class Filtering(Main, Datasets):
    FILTERING_NOTES_LABEL = "Data Cleaning & Filtering Notes"

    FILTERING_PREPARING_MSG = "Datasets are being prepared for Data Cleaning & Filtering"
    
    DATASETS_LABEL = "Datasets"
    INSPECT_LABEL = "Inspect Data"
    FILTERS_LABEL = "Filter Tokens"
    SAMPLES_LABEL = "Samples List"

    FILTERS_FIELDS = "Fields"
    FILTERS_WORDS = "Words"
    FILTERS_POS = "Parts-of-Speech"
    FILTERS_NUM_WORDS = "# of Words"
    FILTERS_PER_WORDS = "% of Words"
    FILTERS_NUM_DOCS = "# of Docs"
    FILTERS_PER_DOCS = "% of Docs"
    FILTERS_NUM_UNIQUEWORDS = "# of Unique Words"

    FILTERS_SPACY_AUTO_STOPWORDS = "Spacy Auto Stop Words"
    FILTERS_TFIDF_MAX = "TF-IDF Max"
    FILTERS_TFIDF_MIN = "TF-IDF Min"

    FILTERS_TFIDF = "TF-IDF"
    FILTERS_ANY = '<ANY>'
    FILTERS_REMOVE = 'Remove'
    FILTERS_INCLUDE = 'Include'
    FILTERS_REMOVE_TOOLTIP = "Add new remove rules based on the "
    FILTERS_READD_TOOLTIP = "Add new include rules based on the "
    FILTERS_REMOVE_ROWS = "Remove Selected Rows"
    FILTERS_REMOVE_ROWS_TOOLTIP = FILTERS_REMOVE_TOOLTIP + "Word and Part-of-Speech pair of selected rows"
    FILTERS_REMOVE_WORDS = "Remove Selected Words"
    FILTERS_REMOVE_WORDS_TOOLTIP = FILTERS_REMOVE_TOOLTIP + "Word of selected rows"
    FILTERS_REMOVE_POS = "Remove Selected Parts-of-Speech"
    FILTERS_REMOVE_POS_TOOLTIP = FILTERS_REMOVE_TOOLTIP + "Part-of-Speech of selected rows"
    FILTERS_ADD_ROWS = "Include Rows"
    FILTERS_ADD_ENTRIES_TOOLTIP = FILTERS_READD_TOOLTIP + "Word and Part-of-Speech of selected rows"
    FILTERS_ADD_WORDS = "Include Selected Words"
    FILTERS_ADD_WORDS_TOOLTIP = FILTERS_READD_TOOLTIP + "Word of selected rows"
    FILTERS_ADD_POS = "Include Selected Part-of-Speech"
    FILTERS_ADD_POS_TOOLTIP = FILTERS_READD_TOOLTIP + "Part-of-Speech of selected rows"
    FILTERS_ENTRIES_LIST = "Entries List"
    FILTERS_ENTRIES_TREEMAP1 = "Top "
    FILTERS_ENTRIES_TREEMAP2 = " Entries (as per # of Words)"
    FILTERS_ENTRIES_TREEMAP_LABEL = "Entries Treemap"
    FILTERS_INCLUDED_LIST = "Included List"
    FILTERS_REMOVED_LIST = "Removed List"
    FILTERS_TOKENIZER = "Tokenizer"
    FILTERS_METHOD = "Method"
    FILTERS_RAWTOKENS = "Raw Tokens"
    FILTERS_STEMMER = "Stemmer"
    FILTERS_LEMMATIZER = "Lemmatizer"
    FILTERS_RULES = "Rules"
    FILTERS_RULES_LIST = "Rules List"
    FILTERS_RULES_STEP = "Step"
    FILTERS_RULES_ACTION = "Action"
    FILTERS_RULES_DELETE = "Delete Rules"
    FILTERS_RULE_DELETE_TOOLTIP = "Selected rules will be deleted"
    FILTERS_RULE_UP = "Move Up"
    FILTERS_RULE_UP_TOOLTIP = "Selected rules will each occur later"
    FILTERS_RULE_DOWN = "Move Down"
    FILTERS_RULE_DOWN_TOOLTIP = "Selected rules will each occur earlier"
    FILTERS_REMOVE_SPACY_AUTO_STOPWORDS = "Remove Spacy Auto Stop Words"
    FILTERS_REMOVE_SPACY_AUTO_STOPWORDS_TOOLTIP = "Add a Remove spaCy Auto Stopwords Rule"

    FILTERS_WORD_SEARCH = "Word Search"
    FILTERS_POS_SEARCH = "Part of Speach Search"

    FILTERS_CREATE_RULE_FIELD = "Field"
    FILTERS_CREATE_RULE_FIELD_TOOLTIP = "leave blank to apply to all fields"
    FILTERS_CREATE_RULE_FIELD_ERROR = "Invalid field selected."
    FILTERS_CREATE_RULE_WORD = "Word"
    FILTERS_CREATE_RULE_WORD_TOOLTIP = "leave blank to apply to all words"
    FILTERS_CREATE_RULE_POS = "Part-of-Speech"
    FILTERS_CREATE_RULE_POS_TOOLTIP = "leave blank to apply to all parts of speech"
    FILTERS_CREATE_RULE_ANY = "<ANY>"
    FILTERS_CREATE_RULE_ACTION = "Action"
    FILTERS_CREATE_RULE_ADVANCED = "Advanced Filters"
    FILTERS_CREATE_TFIDF_REMOVE = 'remove tokens where their tfidf is '
    FILTERS_CREATE_TFIDF_INCLUDE = 'include tokens where their tfidf is '
    FILTERS_CREATE_TFIDF_LOWER = ' in the lower '
    FILTERS_CREATE_TFIDF_UPPER = ' in the upper  '
    FILTERS_CREATE_RULE = "Create Rule"
    FILTERS_CREATE_RULE_TOOLTIP = "Create a new rule at the end of the rules list"
    FILTERS_CREATE_RULE_INVALID_ACTION_ERROR = "Please make sure action has been selected."
    FILTERS_CREATE_RULE_INVALID_ADVANCED_ERROR = "Please make sure a valid advanced choice has been selected."
    FILTERS_CREATE_COUNT_RULE_INCOMPLETE_ADVANCED_ERROR = "Please make sure advanced fields are selected and/or filled out."
    FILTERS_CREATE_COUNT_RULE = "Create Count Rule"
    FILTERS_CREATE_COUNT_RULE_TOOLTIP = "Create a new count rule using either the # of words or the # of documents"
    FILTERS_CREATE_COUNT_RULE_COLUMN_TOOLTIP = "Choose a numeric column"
    FILTERS_CREATE_COUNT_RULE_OPERATION_TOOLTIP = "Choose a comparision operation"
    FILTERS_CREATE_COUNT_RULE_NUMBER_TOOLTIP = "Set the number to compare against"
    FILTERS_CREATE_TFIDF_RULE = "Create TF-IDF Rule"
    FILTERS_CREATE_TFIDF_RULE_TOOLTIP = "Create a new tf-idf rule that uses the individual tokens' tf-idf values"
    FILTERS_CREATE_TFIDF_RULE_NUMBER_TOOLTIP = "Set the percentage cutoff to use to compare against tf-idf values"

    FILTERS_AUTOAPPLY_PAUSE = "Pause Auto-Apply"
    FILTERS_AUTOAPPLY_PAUSE_TOOLTIP = "Pause to prevent rules from automatically applying as the list is changed.\
                                      \nUseful when performing multiple rule changes on millions of words."
    FILTERS_AUTOAPPLY_RESUME = "Resume Auto-Apply"
    FILTERS_AUTOAPPLY_RESUME_TOOLTIP = "Resume to apply all drafted rule changes and enable automatic application of rules as the list is changed.\
                                       \nUseful when performing multiple rule changes on millions of words."
    FILTERS_MANUALAPPLY = "Apply Changes"
    FILTERS_MANUALAPPLY_TOOLTIP = "Will apply any drafted rule changes made to the dataset"
    FILTERS_MANUALCANCEL = "Cancel Changes"
    FILTERS_MANUALCANCEL_TOOLTIP = "Will cancel any drafted rule changes to the dataset"


    FILTERS_IMPORT_CONFIRMATION_REQUEST = "Are you sure you want to proceed with importing rule?"\
                                          "\nWARNING: Any current rules will be lost."
    FILTERS_IMPORT = "Import Rules"
    FILTERS_IMPORT_TOOLTIP = "Import Custom Rules from file"
    FILTERS_EXPORT = "Export Rules"
    FILTERS_EXPORT_TOOLTIP = "Export Custom Rules to file"
    FILTERS_IMPORT_NLTK = "Import NLTK stopwords"
    FILTERS_IMPORT_NLTK_TOOLTIP = "Append nltk stop words to removal list"
    FILTERS_IMPORT_SPACY = "Import spaCy stopwords"
    FILTERS_IMPORT_SPACY_TOOLTIP = "Append spaCy stop words to removal list"

    FILTERS_APPLYING_RULES_BUSY_LABEL = "Applying Rules"
    FILTERS_APPLYING_RULES_STEP = "Applying Filter Rules"
    FILTERS_APPLYING_RULES_GROUP_MSG = "- applied rule group containing:"
    FILTERS_CHANGING_TOKENIZATION_BUSY_LABEL = "Changing Tokenization Method"
    FILTERS_UPDATING_COUNTS_STEP = "Updating Impact Counts"
    
    FILTERS_DISPLAY_STRINGS_BUSY_STEP1 = "Displaying "
    FILTERS_DISPLAY_STRINGS_BUSY_STEP2 = " Strings for Dataset: "

    IMPACT_LABEL = "Impact"


    LOAD_BUSY_MSG_CONFIG = "Loading Data Cleaning & Filtering Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Data Cleaning & Filtering Configurations"

    LOAD_FILTERING_BUSY_MSG = "Loading Data Cleaning & Filtering for dataset: "
    SAVE_FILTERING_BUSY_MSG = "Saving Data Cleaning & Filtering for dataset: "

class Sampling(Samples):
    SAMPLE_NAME_LABEL = "Sample Name "
    SAMPLE_CHANGE_NAME_LABEL = "Change Sample Name"

class Coding(Main):
    CODING_NOTES_LABEL = "Coding Notes"

    LOAD_BUSY_CONFIG_STEP = "Loading Coding Configurations"
    SAVE_BUSY_CONFIG_STEP ="Saving Coding Configurations"

    DATACOLLECTION_LIST = "Data Collection List"

    SHOW_USEFULNESS = "Show Usefulness"
    SHOW_DOCS_FROM = "Show Documents From"

    NAMES = "Names"
    REFERENCES = "References"

    ADD_NEW_CODE= "Add New Code"
    NEW_CODE = "New Code"
    NEW_CODE_TOOLTIP = ""
    ADD_NEW_SUBCODE = "Add New Sub-Code"
    NEW_SUBCODE = "New Sub-Code"
    NEW_SUBCODE_TOOLTIP = ""
    DELETE_CODES = "Delete Codes"
    CONFIRM_DELETE_CODES = "Are you sure you want to delete selected codes?"
    NEW_CODE_BLANK_ERROR = "New code name is blank.\nCodes need to have a name."
    RENAME_CODE_BLANK_ERROR = "Code's new name is blank.\nCodes need to have names."

    ADD_NEW_THEME= "Add New Theme"
    NEW_THEME = "New Theme"
    NEW_THEME_TOOLTIP = ""
    ADD_NEW_SUBTHEME = "Add New Sub-Theme"
    NEW_SUBTHEME = "New Sub-Theme"
    NEW_SUBTHEME_TOOLTIP = ""
    DELETE_THEMES = "Delete Themes"
    CONFIRM_DELETE_THEME = "Are you sure you want to delete selected themes?"
    INCLUDE_CODES = "Include Codes"
    REMOVE_CODES = "Remove Codes"
    NEW_THEME_BLANK_ERROR = "New theme name is blank.\nThemes need to have a name."
    RENAME_THEME_BLANK_ERROR = "Theme's new name is blank.\nThemes need to have names."

    QUOTATIONS = "Quotations"
    PARAPHRASES = "Paraphrases"
    
    CREATE_QUOTATION = "Create Quotation"
    DELETE_QUOTATIONS = "Delete Quotations"
    CONFIRM_DELETE_QUOTATIONS = "Are you sure you want to delete selected quotations?"

class Reviewing(Main):
    DOCUMENTS = "Documents"
    LOAD_BUSY_CONFIG_STEP = "Loading Reviewing Configurations"
    SAVE_BUSY_CONFIG_STEP ="Saving Reviewing Configurations"

class Reporting(Main):
    LOAD_BUSY_CONFIG_STEP = "Loading Reporting Configurations"
    SAVE_BUSY_CONFIG_STEP ="Saving Reporting Configurations"

    THEME_FILTERS = "Filter Themes"
    CODE_FILTERS = "Filter Codes"
    QUOTE_FILTERS = "Filter Quotes"
