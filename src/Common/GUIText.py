#TODO program needs to be adjusted allow french localization
class Common:
    #Common text used everywhere
    WARNING = "Warning"
    ERROR = "Error"
    INFORMATION = "Information"                           

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

    SIZE_WARNING_MSG = "WARNING: may take some time for large datasets"

    MULTIPROCESSING_WARNING_MSG = "A cpu intensive operation is currently in progress."\
                                  "\n Please try current action again after this operation has completed"
    MULTIPROCESSING_CLOSING_MSG = "A cpu intensive operation is currently in progress."\
                                  "\n Are you sure you want to exit the application?"
    
    CONSUMER_KEY = "Consumer Key"
    CONSUMER_SECRET = "Consumer Secret"

class Main(Common):
    APP_NAME = "Computational Thematic Analysis Toolkit"
    UNSAVED = "Unsaved Workspace"

    NEW_WARNING = "You have unsaved changes."\
                  "\nAre you sure you want to creating a new workspace?"\
                  "\nAny unsaved changes will be lost."
    NO_AUTOSAVE_ERROR = "There is no autosave in the app directory."\
                        "\nIf you recently upgraded there may be a save file you can import using the normal load."
    LOAD_WARNING = "You have unsaved changes."\
                   "\nAre you sure you want to load a different workspace?" \
                   "\nAny unsaved changes will be lost."
    LOAD_REQUEST = "Please Choose Workspace to Load"
    LOAD_FAILURE = "Cannot open workspace "
    SAVE_AS_REQUEST = "Please Choose Name for Workspace being Saved"
    SAVE_AS_FAILURE = "Failed to save workspace "
    SAVE_FAILURE = "Failed to save workspace "
    CLOSE_WARNING = "Would you like to save your changes before closing?" \
                   "\nIf skipped any recent changes will be lost."

    NEW_BUSY_LABEL = "Creating New Workspace"
    NEW_BUSY_MSG = "Please Wait while new workspace is created.\n"

    LOAD_BUSY_LABEL = "Loading Workspace"
    LOAD_BUSY_MSG = "Please Wait while data is loaded.\n"
    LOAD_BUSY_MSG_FILE = "Loading File: "
    LOAD_BUSY_MSG_DATASET = "Loaded Dataset: "
    LOAD_BUSY_MSG_SAMPLE = "Loaded Sample: "
    LOAD_BUSY_MSG_CODES = "Loading Codes"
    LOAD_BUSY_MSG_CONFIG = "Loading Configurations."

    SAVE_BUSY_LABEL = "Saving Workspace"
    SAVE_BUSY_MSG = "Please Wait while data is saved.\n"
    AUTO_SAVE_BUSY_MSG = "Please Wait while data is autosaved.\n"
    SAVE_BUSY_MSG_FILE = "Saving File: "
    SAVE_BUSY_MSG_NOTES = "Saving Notes to text."
    SAVE_BUSY_MSG_CONFIG = "Saving Configurations."
    SAVE_BUSY_MSG_DATASETS = "Saving Dataset: "
    SAVE_BUSY_MSG_SAMPLES = "Saving Sample: "
    SAVE_BUSY_MSG_CODES = "Saving Codes"
    SAVE_BUSY_MSG_COMPRESSING = "Writing Saved Data"

    UPGRADE_BUSY_MSG_WORKSPACE1 = "Upgrading Workspace version from  "
    UPGRADE_BUSY_MSG_WORKSPACE2 = " to "
    UPGRADE_BUSY_MSG_DATASETS = "Upgrading Datasets"
    UPGRADE_BUSY_MSG_DATABASE = "Upgrading Database"
    UPGRADE_BUSY_MSG_DATABASE_CREATE = "Converting Workspace to Use Database"
    UPGRADE_BUSY_MSG_SAMPLES = "Upgrading Samples"
    UPGRADE_BUSY_MSG_CODES = "Upgrading Codes"

    SHUTDOWN_BUSY_LABEL = "Shutting Down Application"
    SHUTDOWN_BUSY_POOL = "Shutting down Process Pool"
    
    SAMPLE_CHANGE_NAME = "Change Sample Name"
    NAME_MISSING_ERROR = "Please enter a Name."
    FILENAME_MISSING_ERROR = "Please enter a Filename"
    NAME_DUPLICATE_ERROR = "Same name already exists."\
                           "\nPlease choose a different name."

    DELETE_CONFIRMATION = " will be deleted. Are you sure you want to proceed?"

    CONSUMER_KEY_MISSING_ERROR = "You need to enter a Consumer Key."
    CONSUMER_SECRET_MISSING_ERROR = "You need to enter a Consumer Secret."
    INVALID_CREDENTIALS_ERROR = "Invalid credentials."
    INSUFFICIENT_CREDENTIALS_ERROR = "Your credentials do not allow access to this resource."
    
    OPTIONS_ADVANCED_MODES = "Advanced Modes"
    OPTIONS_MULTIPLEDATASETS = "Allow Multiple Datasets Mode (not yet fully tested)"
    OPTIONS_ADJUSTABLE_LABEL_FIELDS = "Allow adjusting label fields during retrieval"
    OPTIONS_ADJUSTABLE_COMPUTATIONAL_FIELDS = "Allow adjusting computational fields during retrieval"

    #Menu related text
    MODE_MENU = "Mode"
    SHOW_HIDE = "Show/Hide "
    FILE_MENU = "File"
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
    EXIT = "Exit"
    EXIT_TOOLTIP = "Exit Application"
    HELP = "Help"
    ABOUT = "About"

    #About dialog labels
    ABOUT_VERSION = "Version: "
    ABOUT_OSF = "OSF link"
    ABOUT_OSF_URL = "https://osf.io/b72dm/"
    ABOUT_GITHUB = "Github link"
    ABOUT_GITHUB_URL = "https://github.com/rpgauthier/ComputationalThematicAnalysisToolkit"

    #Module/Notes Labels
    GENERAL_LABEL = "General"
    COLLECTION_LABEL = "Data Collection"
    FILTERING_LABEL = "Data Cleaning & Filtering"
    FILTERING_MENU_LABEL = "Data Cleaning && Filtering"
    SAMPLING_LABEL = "Modelling & Sampling"
    SAMPLING_MENU_LABEL = "Modelling && Sampling"
    CODING_LABEL = "Coding"
    REVIEWING_LABEL = "Reviewing"
    REPORTING_LABEL = "Reporting"
    OPTIONS_LABEL = "Options"
    NOTES_LABEL = "Notes"
    TWITTER_LABEL = "Twitter"

class Datasets(Common):

    RETRIEVE_REDDIT_LABEL = "Retrieve New Reddit Dataset"
    RETRIEVE_TWITTER_LABEL = "Retrieve New Twitter Dataset"
    RETRIEVE_CSV_LABEL = "Retrieve New CSV Dataset"
    GROUPED_DATASET_LABEL = "Grouped Dataset Details"
    RETRIEVED_REDDIT_LABEL = "Retrieved Reddit Dataset Details"
    RETRIEVED_CSV_LABEL = "Retrieved CSV Dataset Details"
    NAME_TOOLTIP = "Choose a unique name for the new dataset"
    CONSUMER_KEY_TOOLTIP = "The API key of a project created in the Twitter Developer portal. Do not include quotes."
    CONSUMER_SECRET_TOOLTIP = "The API secret of a project created in the Twitter Developer portal. Do not include quotes."
    START_DATE_TOOLTIP = "Needs to be less than of equal to End Date"
    END_DATE_TOOLTIP = "Needs to be greater than of equal to Start Date"
    DATE_ERROR = "Start Date needs to be before End Date"
    TYPE_ERROR = "Please select a Dataset Type"
    NAME_EXISTS_ERROR = "Name must be unique"
    RETRIEVAL_FAILED_ERROR = "Retrieval failed for one or more datasets.\nPlease try again later."
    RETRIEVAL_FAILED_SUBMISSION = "Failed to retrieve submissions for month "
    RETRIEVAL_FAILED_COMMENT = "Failed to retrieve comments for month "
    NO_RETRIEVAL_CONNECTION_ERROR = "Unable to Connect to Internet.\nPlease check your network status."
    NO_DATA_RETRIEVED_ERROR = "No data retrieved.\nPlease trying again later as requested data may not yet be available."
    NO_DATA_AVAILABLE_ERROR = "No data available.\nPlease try enabling data retrieval."

    REDDIT_ARCHIVED_TOOLTIP = "Use the local subreddit archive to create the dataset."
    REDDIT_UPDATE_PUSHSHIFT_TOOLTIP = "For any part of the period between the start and end dates that the local subreddit archive does not have data,"\
                                       "update the archive using pushshift.io API"\
                                       "\nThen use the archive to create the dataset."\
                                       "\nWARNING: This operation may take between several minutes to hours depending on sizze of existing local subreddit archive"
    REDDIT_FULL_PUSHSHIFT_TOOLTIP = "Remove any existing local subreddit archive."\
                                    "Then retrieve a new archive from pushshift.io API for the period between the start and end dates."\
                                    "Then use the archive to create the dataset"\
                                    "\nWARNING: This operation is a slow and may take several hours"
    REDDIT_UPDATE_REDDITAPI_TOOLTIP = "For any part of the period between the start and end dates that the local subreddit archive does not have data,"\
                                      "update the archive using pushshift.io API"\
                                      "Then update the local subreddit archive for the period between the start and end dates using the Reddit API."\
                                      "Then use the updated archive to create the dataset"\
                                      "\nWARNING: This operation is slow and may take several hours"
    REDDIT_FULL_REDDITAPI_TOOLTIP = "Remove any existing local subreddit archive."\
                                    "Then retrieve a new archive from pushshift.io API for the period between the start and end dates."\
                                    "Then update the archive for the period between the start and end dates using the Reddit API."\
                                    "Then use the updated archive to create the dataset"\
                                    "\nWARNING: This operation is slow and may take several hours"
    REDDIT_SUBMISSIONS_TOOLTIP = "Will retrieve any Reddit submissions between the start and end dates"
    REDDIT_COMMENTS_TOOLTIP = "Will retrieve any Reddit comments between the start and end dates"
    REDDIT_DISCUSSIONS = "Discussions"
    REDDIT_DISCUSSIONS_TOOLTIP = "Will group any Reddit submissions and/or comments retrieved into discussions"
    RETRIVAL_REDDIT_SUBMISSION_ERROR = "an error occured when retrieving Submissions." \
                                               "\nPlease try again later."
    RETRIVAL_REDDIT_COMMENT_ERROR = "an error occured when retrieving Comments."\
                                            "\nPlease try again later."

    RETRIEVING_LABEL = "Retrieval Inprogress for Dataset: "
    RETRIEVING_BEGINNING_MSG = "Please wait while dataset is retrieved.\n"
    RETRIEVING_BUSY_REMOVE_SUBREDDIT_ARCHIVE_MSG = "Deleting local archive for subreddit: "
    RETRIEVING_BUSY_PUSHSHIFT_DATA = "Retrieving Data from Pushshift"
    RETRIEVING_BUSY_DOWNLOADING_SUBMISSIONS_MSG = "Preparing to download Submission Data"
    RETRIEVING_BUSY_DOWNLOADING_COMMENTS_MSG = "Preparing to download Comment Data"
    RETRIEVING_BUSY_DOWNLOADING_TWITTER_TWEETS_MSG = "Preparing to download Twitter tweets data"
    RETRIEVING_BUSY_DOWNLOADING_ALL_MSG = "Downloading all data for month: "
    RETRIEVING_BUSY_DOWNLOADING_NEW_MSG = "Downloading new data for month: "
    RETRIEVING_BUSY_IMPORTING_SUBMISSION_MSG = "Importing required submission data"
    RETRIEVING_BUSY_IMPORTING_COMMENT_MSG = "Importing required comment data"
    RETRIEVING_BUSY_IMPORTING_TWITTER_TWEET_MSG = "Importing required Twitter tweets data"
    RETRIEVING_BUSY_IMPORTING_FILE_MSG = "Importing from file: "
    RETRIEVING_BUSY_PREPARING_DISCUSSION_MSG = "Preparing Discussion Data for Application use"
    RETRIEVING_BUSY_PREPARING_SUBMISSION_MSG = "Preparing Submission Data for Application use"
    RETRIEVING_BUSY_PREPARING_COMMENT_MSG = "Preparing Comment Data for Application use."
    RETRIEVING_BUSY_SEARCHING_DATA_MSG1 = "Selecting Data that contains ["
    RETRIEVING_BUSY_SEARCHING_DATA_MSG2 = "] in a text field."
    
    RETRIEVING_BUSY_PREPARING_CSV_MSG = "Preparing CSV Data for Application use."
    RETRIEVING_BUSY_PREPARING_TWITTER_MSG = "Preparing Twitter Data for Application use."
    RETRIEVING_BUSY_CONSTRUCTING_MSG = "Datasets are being constructed."

    TWITTER_RATE_LIMIT_REACHED_MSG = "Warning: Twitter API rate limit has been reached. The number of tweets will be shortened."

    TOKENIZING_BUSY_STARTING_FIELD_MSG = "Starting to tokenize field: "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG1 = "Completed tokenizing "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG2 = " of "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG3 = " for field: "
    TOKENIZING_BUSY_STARTING_TFIDF_MSG = "Starting to calculate TFIDF values"
    TOKENIZING_BUSY_COMPLETED_TFIDF_MSG = "Completed to calculating TFIDF values"

    CHANGING_NAME_BUSY_LABEL = "Changing Name"
    CHANGING_NAME_BUSY_PREPARING_MSG = "Preparing to Update Dataset Name\n"
    CHANGING_NAME_BUSY_MSG1 = "Changing From: "
    CHANGING_NAME_BUSY_MSG2 = " To: "

    CHANGING_LANGUAGE_BUSY_LABEL = "Changing Language"
    CHANGING_LANGUAGE_BUSY_PREPARING_MSG = "Preparing to Update Dataset Language\n"


    REFRESHING_DATASETS_BUSY_MSG = "Refreshing Data for Dataset: "

    #common Fields
    DESCRIPTION = "Description"
    DOCUMENT_NUM = "# of Documents"
    RETRIEVED_ON = "Retrieved On"
    IMPORTED_ON = "Imported On"
    PREPARED_ON = "Prepared On"
    LANGUAGE = "Language"
    QUERY = "Query"
    SEARCH_BY = "Search by"
    KEYWORDS = "Keywords"
    HASHTAGS = "Hashtags"
    ACCOUNTS = "Accounts"

    #Retrieval specific fields
    DATASET_CONFIGURATIONS = "Dataset Configurations"
    DATA_CONSTRAINTS = "Data Constraints"
    SPECIAL_DATA_FIELDS = "Special Data Fields"
    ETHICAL_CONSIDERATIONS = "Ethical Considerations"
    START_DATE = "Start Date"
    END_DATE = "End Date"
    START_DATETIME = "Start Date & Time"
    END_DATETIME = "End Date & Time"
    UTC = "UTC"

    REDDIT_LABEL = "Reddit"
    REDDIT_SUBREDDIT = "www.reddit.com/r/"
    REDDIT_SUBREDDIT_TOOLTIP = "Exact case-sensitive spelling of the subreddit for retrieval."\
                               "\nIf you require multiple subreddits in the same dataset then seperate the subreddit names by comma."
    REDDIT_SUBREDDIT_MISSING_ERROR = "Please enter a Subreddit."
    REDDIT_SUBMISSIONS = "Submissions"
    REDDIT_COMMENTS = "Comments"
    REDDIT_SUBMISSIONS_NUM = "# of Submissions"
    REDDIT_COMMENTS_NUM = "# of Comments"
    REDDIT_CONTAINS_TEXT = "Contains Text"

    REDDIT_ARCHIVED = "Local Subreddit Archive"
    REDDIT_UPDATE_PUSHSHIFT = "Local Subreddit Archive updated using Pushshift.io"
    REDDIT_FULL_PUSHSHIFT = "Full retrieval from Pushshift.io"
    
    REDDIT_UPDATE_REDDITAPI = "Local Subreddit Archive and updated using Pushshift.io and Reddit API"
    REDDIT_FULL_REDDITAPI = "Full retrieved from Pushshift.io and updated using Reddit API"

    TWITTER_LABEL = "Twitter"
    TWITTER_TWEETS_NUM = "# of Tweets"
    TWITTER_QUERY_HYPERLINK = "https://developer.twitter.com/en/docs/twitter-api/v1/tweets/search/guides/standard-operators"
    TWITTER_QUERY_TOOLTIP = "Query needs to follow these rules: " + TWITTER_QUERY_HYPERLINK
    TWITTER_QUERY_RADIOBUTTON_TOOLTIP = "Use a Twitter query to create the dataset, using these rules: " + TWITTER_QUERY_HYPERLINK
    TWITTER_QUERY_MISSING_ERROR = "You need to enter a query."
    TWITTER_QUERY_PLACEHOLDER = "ex. life OR technology from:google"
    TWITTER_TWEET_ATTRIBUTES = "Tweet Attributes"
    TWITTER_TWEET_ATTRIBUTES_RADIOBUTTON_TOOLTIP = "Use specific tweet attributes to create the dataset."
    TWITTER_KEYWORDS_PLACEHOLDER = "ex. COVID vaccine, health, safety"
    TWITTER_HASHTAGS_PLACEHOLDER = "ex. #toronto, #raptors"
    TWITTER_ACCOUNT_PLACEHOLDER = "ex. JustinTrudeau"

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
    DATASET_DELETE = "Delete this dataset from the workspace"
    CUSTOMIZE_LABEL_FIELDS = "Customize Label Fields"
    CUSTOMIZE_COMPUTATIONAL_FIELDS = "Customize Computational Fields"

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
    DELETE_TOOLTIP = "Remove selected sample from workspace"
    
    DELETE_SAMPLE = "Delete Sample"
    DELETE_SAMPLE_CONFIRM1 = "Are you sure you want to delete sample: "
    DELETE_SAMPLE_CONFIRM2 = "\nWARNING this action cannot be undone."

    DELETE_TOPIC = "Delete Topic"
    CONFIRM_DELETE_TOPIC1 = "Are you sure you want to delete the topic: "
    CONFIRM_DELETE_TOPIC2 = "\nWARNING this action cannot be undone."

    MERGE_TOPIC_LABEL = "Merge Topics"
    MERGE_TOPIC_SHORTHELP = "Create a new Merged Topic from selected Topics"
    SPLIT_TOPIC_LABEL = "Split Topics"
    SPLIT_TOPIC_SHORTHELP = "Remove selected topics from their Merged Topic"
    REMOVE_TOPIC_LABEL = "Remove Topics"
    REMOVE_TOPIC_SHORTHELP = "Remove selected topics from the model"
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
    GENERATING_PREPARING_MSG = "\nDatasets are being prepared"
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
    DELETING_BUSY_REMOVING_MSG = "Deleting Dataset: "

    ADDING_COMPUTATIONAL_FIELDS_BUSY_LABEL = "Adding Computational Fields"
    ADDING_LABEL_FIELDS_BUSY_LABEL = "Adding Label Fields"
    ADDING_FIELDS_BUSY_PREPARING_MSG = "Preparing to Add Selected Fields"
    ADDING_FIELDS_BUSY_MSG = "Adding Selection: "

    REMOVING_COMPUTATIONAL_FIELDS_BUSY_LABEL = "Removing Computational Fields"
    REMOVING_LABEL_FIELDS_BUSY_LABEL = "Removing Label Fields"
    REMOVING_FIELDS_BUSY_PREPARING_MSG = "Preparing to Remove Selected Fields"
    REMOVING_FIELDS_BUSY_MSG = "Removing Selection: "

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

    FILTERS_PREPARING_MSG = "Please wait while datasets are prepared for token filtering for field: "
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
    FILTERS_APPLYING_RULES_BUSY_MSG = "Applying Filter Rules"
    FILTERS_CHANGING_TOKENIZATION_BUSY_LABEL = "Changing Tokenization Method"
    FILTERS_UPDATING_COUNTS = "Updating Impact Counts"
    
    FILTERS_DISPLAY_STRINGS_BUSY_MSG1 = "Displaying "
    FILTERS_DISPLAY_STRINGS_BUSY_MSG2 = "Strings for Dataset: "

    IMPACT_LABEL = "Impact"


    LOAD_BUSY_MSG_CONFIG = "Loading Data Cleaning & Filtering Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Data Cleaning & Filtering Configurations"

    LOAD_FILTERING_BUSY_MSG = "Loading Data Cleaning & Filtering for dataset: "
    SAVE_FILTERING_BUSY_MSG = "Saving Data Cleaning & Filtering for dataset: "

class Sampling(Samples):
    SAMPLE_NAME = "Sample Name "

class Coding(Main):
    CODING_NOTES_LABEL = "Coding Notes"

    LOAD_BUSY_MSG_CONFIG = "Loading Coding Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Coding Configurations"

    DATACOLLECTION_LIST = "Data Collection List"

    SHOW_USEFULNESS = "Show Usefulness"
    SHOW_DOCS_FROM = "Show Documents From"

    REFERENCES = "References"

    ADD_NEW_CODE= "Add New Code"
    NEW_CODE = "New Code"
    NEW_CODE_TOOLTIP = ""
    ADD_NEW_SUBCODE = "Add New Sub-Code"
    NEW_SUBCODE = "New Sub-Code"
    NEW_SUBCODE_TOOLTIP = ""
    DELETE_CODES = "Delete Codes"
    CONFIRM_DELETE_CODES = "Are you sure you want to delete selected codes?"
    CHANGE_COLOUR = "Change Colour"

    NEW_CODE_BLANK_ERROR = "New code name is blank.\nCodes need to have a name."
    RENAME_CODE_BLANK_ERROR = "Code's new name is blank.\nCodes need to have names."

    CREATE_QUOTATION = "Create Quotation"

    QUOTATIONS = "Quotations"
    PARAPHRASES = "Paraphrases"

    DELETE_QUOTATIONS = "Delete Quotations"
    CONFIRM_DELETE_QUOTATIONS = "Are you sure you want to delete selected quotations?"

    LOAD_BUSY_MSG_CONFIG = "Loading Coding Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Coding Configurations"

    CODES_IMPORT = "Import REFI-QDA Codebook"
    CODES_IMPORT_TOOLTIP = "Import Codes from file that follows the REFI-QDA Codebook specifications"
    CODES_IMPORT_CONFIRMATION_REQUEST = "Please confirm you wish to import an external codebook file into this project."\
                                        "\nWARNING: Existing codes may be updated if they had previously been exported or imported and are present in the external codebook"
    CODES_EXPORT = "Export REFI-QDA Codebook"
    CODES_EXPORT_TOOLTIP = "Export Codes to a file that follows the REFI-QDA Codebook specifications"
    

class Reviewing(Main):
    LOAD_BUSY_MSG_CONFIG = "Loading Reviewing Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Reviewing Configurations"

class Reporting(Main):
    LOAD_BUSY_MSG_CONFIG = "Loading Reporting Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Reporting Configurations"

    CODE_FILTERS = "Filter Codes"
    QUOTE_FILTERS = "Filter Quotes"
