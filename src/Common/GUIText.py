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
    CANCEL = "Cancel"

    ADD = "Add"
    REMOVE = "Remove"
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

class Main(Common):
    APP_NAME = "Computational Thematic Analysis Toolkit"

    NEW_WARNING = "Are you sure you wnat to proceed with creating a new workspace?"\
                  "\nAny unsaved changes will be lost."
    LOAD_WARNING = "Are you sure you want to proceed with loading a workspace?" \
                   "\nAny unsaved changes will be lost."
    LOAD_REQUEST = "Please Choose Workspace to Load"
    LOAD_FAILURE = "Cannot open workspace "
    SAVE_AS_REQUEST = "Please Choose Name for Workspace being Saved"
    SAVE_AS_FAILURE = "Failed to save workspace "
    SAVE_FAILURE = "Failed to save workspace "
    CLOSE_WARNING = "Would you like to save your changes before closing?" \
                   "\nIf you do not save any recent changes will be lost."

    NEW_BUSY_LABEL = "Creating New Workspace"
    NEW_BUSY_MSG = "Please Wait while new workspace is created.\n"

    LOAD_BUSY_LABEL = "Loading Workspace"
    LOAD_BUSY_MSG = "Please Wait while data is loaded.\n"
    LOAD_BUSY_MSG_DATASET = "Loading Dataset: "
    LOAD_BUSY_MSG_SAMPLE = "Loading Sample: "
    LOAD_BUSY_MSG_CONFIG = "Loading Configurations."

    SAVE_BUSY_LABEL = "Saving Workspace"
    SAVE_BUSY_MSG = "Please Wait while data is saved.\n"
    SAVE_BUSY_MSG_NOTES = "Saving Notes to text."
    SAVE_BUSY_MSG_CONFIG = "Saving Configurations."
    SAVE_BUSY_MSG_DATASETS = "Saving Dataset: "
    SAVE_BUSY_MSG_SAMPLES = "Saving Sample: "

    SHUTDOWN_BUSY_LABEL = "Shutting Down Application"
    SHUTDOWN_BUSY_POOL = "Shutting down Process Pool"
    
    NAME_MISSING_ERROR = "You must enter a Name."
    FILENAME_MISSING_ERROR = "You must enter a Filename"
    NAME_DUPLICATE_ERROR = "Same name already exists."\
                           "\nPlease choose a different name."

    DELETE_CONFIRMATION = " will be deleted. Are you sure you want to proceed?"

    OPTIONS_ADVANCED_MODES = "Advanced Modes"
    OPTIONS_MULTIPLEDATASETS = "Allow Multiple Datasets Mode (not yet fully tested)"
    OPTIONS_ADJUSTABLE_METADATA = "Allow adjusting metadata during retrieval"
    OPTIONS_ADJUSTABLE_INCLUDEDFIELDS = "Allow adjusting included fields during retrieval"

    #Menu related text
    MODE_MENU = "Mode"
    VIEW_MENU = "View"
    SHOW_HIDE = "Show/Hide "
    FILE_MENU = "File"
    NEW = "New"
    NEW_TOOLTIP = "Create a New Workspace"
    LOAD = "Load"
    LOAD_TOOLTIP = "Load an Existing Workspace"
    SAVE = "Save"
    SAVE_TOOLTIP = "Save Current Workspace"
    SAVE_AS = "Save As"
    SAVE_AS_TOOLTIP = "Save the Current Workspace with a new name"
    EXIT = "Exit"
    EXIT_TOOLTIP = "Exit Application"

    #Module/Notes Labels
    GENERAL_LABEL = "General"
    COLLECTION_LABEL = "Data Collection"
    FILTERING_LABEL = "Data Cleaning & Filtering"
    FILTERING_MENU_LABEL = "Data Cleaning && Filtering"
    SAMPLING_LABEL = "Sampling & Modelling"
    SAMPLING_MENU_LABEL = "Sampling && Modelling"
    CODING_LABEL = "Coding"
    REVIEWING_LABEL = "Reviewing"
    REPORTING_LABEL = "Reporting"
    OPTIONS_LABEL = "Options"
    NOTES_LABEL = "Notes"

class Datasets(Common):

    RETRIEVE_REDDIT_LABEL = "Retrieve New Reddit Dataset"
    RETRIEVE_CSV_LABEL = "Retrieve New CSV Dataset"
    GROUPED_DATASET_LABEL = "Grouped Dataset Details"
    RETRIEVED_REDDIT_LABEL = "Retrieved Reddit Dataset Details"
    RETRIEVED_CSV_LABEL = "Retrieved CSV Dataset Details"
    NAME_TOOLTIP = "Choose a unique name for the new dataset"
    START_DATE_TOOLTIP = "Must less than of equal to End Date"
    END_DATE_TOOLTIP = "Must greater than of equal to Start Date"
    DATE_ERROR = "Start Date must be before End Date"
    TYPE_ERROR = "Dataset Type must be selected"
    NAME_EXISTS_ERROR = "Name must be unique"
    RETRIEVAL_FAILED_ERROR = "Retrieval failed for one or more datasets.\nPlease try again later."
    NO_RETRIEVAL_CONNECTION_ERROR = "Unable to Connect to Internet.\nPlease check your network status."
    NO_DATA_RETRIEVED_ERROR = "No data retrieved.\nPlease trying again later as requested data may not yet be avaliable."
    NO_DATA_AVALIABLE_ERROR = "No data avaliable.\nPlease try enabling data retrieval."

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

    GROUP_REQUEST = "Choose Field to use when Grouping "
    GROUP_REQUEST_ERROR = 'You must select a single field to group data on'

    RETRIEVING_LABEL = "Retrieval Inprogress for Dataset: "
    RETRIEVING_BEGINNING_MSG = "Please wait while dataset is retrieved.\n"
    RETRIEVING_BUSY_REMOVE_SUBREDDIT_ARCHIVE_MSG = "Deleting local archive for subreddit: "
    RETRIEVING_BUSY_PUSHSHIFT_DATA = "Retrieving Data from Pushshift"
    RETRIEVING_BUSY_DOWNLOADING_SUBMISSIONS_MSG = "Preparing to download Submission Data"
    RETRIEVING_BUSY_DOWNLOADING_COMMENTS_MSG = "Preparing to download Comment Data"
    RETRIEVING_BUSY_DOWNLOADING_ALL_MSG = "Downloading all data for month: "
    RETRIEVING_BUSY_DOWNLOADING_NEW_MSG = "Downloading new data for month: "
    RETRIEVING_BUSY_IMPORTING_SUBMISSION_MSG = "Importing required submission data"
    RETRIEVING_BUSY_IMPORTING_COMMENT_MSG = "Importing required comment data"
    RETRIEVING_BUSY_IMPORTING_FILE_MSG = "Importing from file: "
    RETRIEVING_BUSY_PREPARING_DISCUSSION_MSG = "Preparing Discussion Data for Application use"
    RETRIEVING_BUSY_PREPARING_SUBMISSION_MSG = "Preparing Submission Data for Application use"
    RETRIEVING_BUSY_PREPARING_COMMENT_MSG = "Preparing Comment Data for Application use."
    RETRIEVING_BUSY_PREPARING_CSV_MSG = "Preparing CSV Data for Application use."
    RETRIEVING_BUSY_CONSTRUCTING_MSG = "Datasets are being constructed."

    TOKENIZING_BUSY_STARTING_FIELD_MSG = "Starting to tokenize field: "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG1 = "Completed tokenizing "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG2 = " of "
    TOKENIZING_BUSY_COMPLETED_FIELD_MSG3 = " for field: "

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
    PREPARED_ON = "Prepared On"
    LANGUAGE = "Language"

    #Retrieval specific fields
    START_DATE = "Start Date"
    END_DATE = "End Date"
    REDDIT_LABEL = "Reddit"
    REDDIT_SUBREDDIT = "Subreddit"
    REDDIT_SUBREDDIT_TOOLTIP = "Exact case-sensitive spelling of the subreddit for retrieval"
    REDDIT_SUBREDDIT_MISSING_ERROR = "You must enter a Subreddit."
    REDDIT_SUBMISSIONS = "Submissions"
    REDDIT_COMMENTS = "Comments"

    REDDIT_ARCHIVED = "Local Subreddit Archive"
    REDDIT_UPDATE_PUSHSHIFT = "Local Subreddit Archive updated using Pushshift.io"
    REDDIT_FULL_PUSHSHIFT = "Full retrieval from Pushshift.io"
    
    REDDIT_UPDATED_REDDITAPI = "Local Subreddit Archive and updated using Pushshift.io and Reddit API"
    REDDIT_FULL_REDDITAPI = "Full retrieved from Pushshift.io and updated using Reddit API"

    CSV_LABEL = "CSV"
    CSV_DATASETFIELD = "Dataset Field: "
    CSV_DATASETFIELD_TOOLTIP = "If the csv file contains data from a single source leave this field blank."\
                          "If the csv file contains multiple sources please choose a field differentiates those sources.\n"\
                          "This is important if dealing with multiple languages as different processing may be required."
    CSV_IDFIELD = "Id Field: "
    CSV_IDFIELD_TOOLTIP = "Choose a field to use as id to documents.\n"\
                          "If id is unique then every row will be treated as a document.\n"\
                          "If id is not unique, rows with the same id will be merged."
    CSV_IDFIELD_MISSING_ERROR = "You must choose an field to use as an id."
    CSV_IDFIELD_DEFAULT = "<Assign based on Row Number>"
    CSV_URLFIELD = "URL Field: "
    CSV_URLFIELD_TOOLTIP = "Choose a field to use as url to link to the online version of the documents."
    CSV_DATETIMEFIELD = "Datetime Field: "
    CSV_DATETIMEFIELD_TOOLTIP = "Choose a field to use as datetime to documents."
    CSV_DATETIMETZ_MISSING_ERROR = "Need to choose the time zone for the contents of the datatime field"
    
    METADATAFIELDS = "Metdata Fields: "
    METADATAFIELDS_TOOLTIP = "Choose additional fields you need to use when identifying and interpret the data."
    INCLUDEDFIELDS = "Included Fields: "
    INCLUDEDFIELDS_TOOLTIP = "Choose fields you want machine learning to use when identifing samples of interest from the CSV file."

class Samples(Main):
    #Model types
    RANDOM_LABEL = "Random"
    LDA_LABEL = "Latent Dirchlet Allocation"
    BITERM_LABEL = "Biterm"
    NMF_LABEL = "Non-Negative Matrix Factorization"

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
    DELETE_CONFIRMATION_WARNING = "Are you sure you want to delete this sample?"\
                                  "\nWARNING this action cannot be undone."


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

    NOT_SAVED_WARNING = "You must save the workspace to generate an LDA Model"
    INPROGRESS = "Inprogress"
    CHECK_STATUS = "Check Status"
    CHECK_STATUS_TOOLTIP = "Check if Model is Ready"

    NAME_TOOLTIP = "Name must be unique, lowercase, and have no spaces."
    NUMBER_OF_TOPICS_CHOICE = "Choose Number of Topics: "
    NUMBER_OF_TOPICS_TOOLTIP = "Modelling more topics takes longer but may help identify less common topics"
    NUMBER_OF_TOPICS = "Number of Topics: "
    NUMBER_OF_PASSES_CHOICE = "Choose Number of Passes: "
    NUMBER_OF_PASSES_TOOLTIP = "More passes causes modelling to take longer but may help produce more cohesive topics"
    NUMBER_OF_PASSES = "Number of Passes: "
    NUMBER_OF_DOCUMENTS = "Number of Documents: "
    DATASET = Datasets.DATASET
    DATASET_MISSING_ERROR = "Dataset was not chosen." \
                            "\nPlease choose a dataset for the model."
    DATASET_NOTAVALIABLE_ERROR = "No Data is avaliable." \
                            "\nPlease load data into the project before trying to create a model."
    

    GENERATE_WARNING = "\nWARNING: Do not shut down program or else model will not be created."
    GENERATE_NOTSAVED_WARNING = "Workspace has not yet been saved."\
                                "\nTo generate this type of sample you must save the workspace"
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
    ETHICS_CONFIRMATION = "We have considered "
    ETHICS_CONFIRMATION_MISSING_ERROR = "Before proceeding we need to take time to consider "
    ETHICS_COMMUNITY1 = "the online community's guidlines, rules, and terms of use."
    ETHICS_COMMUNITY2 = "the impact of our project on the online community."
    ETHICS_RESEARCH = "the research community's ethical guidlines and rules on online public data collection."
    ETHICS_INSTITUTION = "our institution's ethical guidlines and rules on online public data collection."
    ETHICS_REDDIT = "Reddit's rules and terms of use for collecting data."
    ETHICS_REDDIT_URL = "https://www.redditinc.com/policies/"
    ETHICS_REDDITAPI_URL = "https://www.reddit.com/wiki/api-terms"
    ETHICS_PUSHSHIFT = "that this toolkit uses the Pushshift.io api to collect Reddit Data."

    DATASETSLIST_LABEL = "Datasets List"
    DATASETS_RETRIEVE_LABEL = "Retrieve"
    DATASETS_RETRIEVE_TOOLTIP = "Retrieve new datasets for workspace"
    DATASETS_RETRIEVE_REDDIT = "Retrieve " + Datasets.REDDIT_LABEL
    DATASETS_RETRIEVE_REDDIT_TOOLTIP = "Retrieve new Reddit datasets for workspace"
    DATASETS_RETRIEVE_CSV = "Retrieve " + Datasets.CSV_LABEL
    DATASETS_RETRIEVE_CSV_TOOLTIP = "Retrieve new CSV datasets for workspace"
    DATASETS_GROUP_TOOLTIP = "Selected datasets will be grouped"
    DATASETS_GROUP_NAME = "Group Name:"
    DATASETS_UNGROUP_TOOLTIP = "Selected datasets will be ungrouped"
    DATASETS_DELETE_TOOLTIP = "Selected datasets will be removed"
    DATASETS_DELETE_CONFIRMATION_WARNING = "\nWARNING this action can only be undone by adding new datasets."

    DATASETSDATA_LABEL = "Dataset Data"
    VIEW_DETAILS = "View Details"
    CUSTOMIZE_FIELDS = "Customize Fields"

    FIELDS_LABEL = "Fields"
    FIELDS_AVALIABLE_LABEL = "Avaliable Fields"
    FIELDS_CHOSEN_LABEL = 'Chosen Fields'
    FIELDS_ADD_TOOLTIP = "Selected fields will be added to Chosen Fields"
    FIELDS_REMOVE_TOOLTIP = "Selected fields will be removed from Chosen Fields"
    FIELDS_EXISTS_ERROR = "Chosen Fields already has field: "
    FIELDS_MERGE_ERROR = "Can only merge fields and selected fields must be from the same dataset or datasets that are grouped together."
    FIELDS_REMOVE_DATASET_WARNING = "Are you sure you want to remove all chosen fields and under Dataset: "

    GROUPING_BUSY_LABEL = "Grouping Datasets"
    GROUPING_BUSY_PREPARING_MSG = "Preparing to Group Selected Datasets"
    GROUPING_BUSY_CREATING_MSG = "Creating new Grouped Dataset: "
    GROUPING_BUSY_ADDING_MSG1 = "Adding Dataset: "
    GROUPING_BUSY_ADDING_MSG2 = " to Grouped Dataset: "
    GROUPING_BUSY_UPDATING_MSG = "Updating metadata for Grouped Dataset: "

    UNGROUPING_BUSY_LABEL = "Ungrouping Datasets"
    UNGROUPING_BUSY_PREPARING_MSG = "Preparing to Ungroup Selected Datasets"
    UNGROUPING_BUSY_REMOVING_MSG1 = "Ungrouping Dataset: "
    UNGROUPING_BUSY_REMOVING_MSG2 = " from Grouped Dataset: "
    UNGROUPING_BUSY_UPDATING_MSG = "Updating metadata for Grouped Dataset: "

    DELETING_BUSY_LABEL = "Deleting Datasets"
    DELETING_BUSY_PREPARING_MSG = "Preparing to Delete Selected Datasets"
    DELETING_BUSY_REMOVING_MSG = "Deleting Dataset: "
    DELETING_BUSY_UPDATING_MSG = "Updating metadata for Grouped Dataset: "

    ADDING_FIELDS_BUSY_LABEL = "Adding Fields"
    ADDING_FIELDS_BUSY_PREPARING_MSG = "Preparing to Add Selected Fields"
    ADDING_FIELDS_BUSY_MSG = "Adding Selection: "

    REMOVING_FIELDS_BUSY_LABEL = "Removing Fields"
    REMOVING_FIELDS_BUSY_PREPARING_MSG = "Preparing to Remove Selected Fields"
    REMOVING_FIELDS_BUSY_MSG = "Removing Selection: "

    UPDATING_DATASET_BUSY_MSG = "Updating Data Collection's Dataset Panel"

    LOAD_BUSY_MSG_CONFIG = "Loading Data Collection Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Data Collection Configurations"

#relies on Datasets, Main, and Common being imported by models
class Filtering(Main, Datasets):
    FILTERING_NOTES_LABEL = "Data Cleaning & Filtering Notes"

    FILTERING_PREPARING_MSG = "Datasets are being prepared for Data Cleaning & Filtering"
    #DATASETS_NAME_EXISTS_WARNING = " already exists in Data Cleaning and Filtering Module."\
    #                               "\nIf you proceed with importing, the existing data will be replaced."\
    #                               "\nAre you sure you want to proceed with importing?"
    #DATASETS_DELETE_TOOLTIP = "Selected datasets will be removed"
    #DATASETS_DELETE_CONFIRMATION_WARNING = "\nWARNING this action cannot be undone."
    #DATASETS_DELETE_GROUPED_ERROR1 = "Cannot delete dataset: "
    #DATASETS_DELETE_GROUPED_ERROR2 = "\nThis dataset is part of a group due to data preperation approach."\
    #                                 "\nPlease consider removing the group and preparing other datasets in previous module."

    DATASETS_LABEL = "Datasets"
    INSPECT_LABEL = "Inspect Data"
    FILTERS_LABEL = "Filter Tokens"
    SAMPLES_LABEL = "Samples List"

    FILTERS_PREPARING_MSG = "Please wait while datasets are prepared for token filtering for field: "
    FILTERS_ENTRIES = "Entries"
    FILTERS_FIELDS = "Fields"
    FILTERS_WORDS = "Words"
    FILTERS_POS = "Parts of Speech"
    FILTERS_NUM_WORDS = "# of Words"
    FILTERS_PER_WORDS = "% of Words"
    FILTERS_NUM_DOCS = "# of Docs"
    FILTERS_PER_DOCS = "% of Docs"
    FILTERS_NUM_UNIQUEWORDS = "# of Unique Words"

    FILTERS_SPACY_AUTO_STOPWORDS = "Spacy Auto Stop Words"
    FILTERS_TFIDF = "TFIDF Range"
    FILTERS_ANY = '<ANY>'
    FILTERS_REMOVE = 'Remove'
    FILTERS_INCLUDE = 'Include'
    FILTERS_REMOVE_TOOLTIP = "Remove selection based on "
    FILTERS_READD_TOOLTIP = "Readd selection based on "
    FILTERS_REMOVE_ENTRIES = "Remove " + FILTERS_ENTRIES
    FILTERS_REMOVE_ENTRIES_TOOLTIP = FILTERS_REMOVE_TOOLTIP + FILTERS_ENTRIES
    FILTERS_REMOVE_WORDS = "Remove " + FILTERS_WORDS
    FILTERS_REMOVE_WORDS_TOOLTIP = FILTERS_REMOVE_TOOLTIP + FILTERS_WORDS
    FILTERS_REMOVE_POS = "Remove " + FILTERS_POS
    FILTERS_REMOVE_POS_TOOLTIP = FILTERS_REMOVE_TOOLTIP + FILTERS_POS
    FILTERS_READD_ENTRIES = "Readd " + FILTERS_ENTRIES
    FILTERS_READD_ENTRIES_TOOLTIP = FILTERS_READD_TOOLTIP + FILTERS_ENTRIES
    FILTERS_READD_WORDS = "Readd " + FILTERS_WORDS
    FILTERS_READD_WORDS_TOOLTIP = FILTERS_READD_TOOLTIP + FILTERS_WORDS
    FILTERS_READD_POS = "Readd " + FILTERS_POS
    FILTERS_READD_POS_TOOLTIP = FILTERS_READD_TOOLTIP + FILTERS_POS
    FILTERS_ENTRIES_LIST = "Entries List"
    FILTERS_ENTRIES_TREEMAP1 = "Top "
    FILTERS_ENTRIES_TREEMAP2 = " Entries (as per # of Words)"
    FILTERS_ENTRIES_TREEMAP_LABEL = "Entries Treemap"
    FILTERS_INCLUDED = "Included "
    FILTERS_REMOVED = "Removed "
    FILTERS_TOKENIZER = "Tokenizer:"
    FILTERS_METHOD = "Method:"
    FILTERS_RAWTOKENS = "Raw Tokens"
    FILTERS_STEMMER = "Stemmer: "
    FILTERS_LEMMATIZER = "Lemmatizer: "
    FILTERS_RULES = "Rules"
    FILTERS_RULES_STEP = "Sequence"
    FILTERS_RULES_ACTION = "Action"
    FILTERS_RULE_REMOVE_TOOLTIP = "Selected rules will be removed"
    FILTERS_RULE_INCREASE = "Move Later"
    FILTERS_RULE_INCREASE_TOOLTIP = "Selected rules will each occur later"
    FILTERS_RULE_DECREASE = "Move Earlier"
    FILTERS_RULE_DECREASE_TOOLTIP = "Selected rules will each occur earlier"
    FILTERS_REMOVE_SPACY_AUTO_STOPWORDS = "Remove Spacy Auto Stop Words"
    FILTERS_REMOVE_SPACY_AUTO_STOPWORDS_TOOLTIP = "Add a Remove spaCy Auto Stopwords Rule"

    FILTERS_CREATE_RULE_FIELD = "Apply to Field:"
    FILTERS_CREATE_RULE_FIELD_TOOLTIP = "leave blank to apply to all fields"    
    FILTERS_CREATE_RULE_WORD = "Apply to Word:"
    FILTERS_CREATE_RULE_WORD_TOOLTIP = "leave blank to apply to all words"
    FILTERS_CREATE_RULE_POS = "Apply to POS:"
    FILTERS_CREATE_RULE_POS_TOOLTIP = "leave blank to apply to any pos"
    FILTERS_CREATE_RULE_RULE = "Rule:"
    FILTERS_CREATE_COUNT_RULE = "Create Count Rule"
    FILTERS_CREATE_COUNT_RULE_TOOLTIP = "Create a New Count Rule"
    FILTERS_CREATE_COUNT_RULE_COLUMN_TOOLTIP = "Choose a numeric column"
    FILTERS_CREATE_COUNT_RULE_OPERATION_TOOLTIP = "Choose a comparision operation"
    FILTERS_CREATE_COUNT_RULE_NUMBER_TOOLTIP = "Set the number to compare against"
    FILTERS_CREATE_COUNT_RULE_INCOMPLETE_ERROR = "Incomplete count rule.\nPlease make sure all Rule fields are filled out."
    FILTERS_CREATE_TFIDF_RULE = "Create TFIDF Rule"
    FILTERS_CREATE_TFIDF_RULE_TOOLTIP = "Create a New TFIDF Rule"
    FILTERS_CREATE_TFIDF_RULE_NUMBER_TOOLTIP = "Set the token rank to use when deciding what tfidf value to use"
    FILTERS_CREATE_TFIDF_RULE_INCOMPLETE_ERROR = "Incomplete tfidf rule.\nPlease make sure all Rule fields are filled out."

    FILTERS_IMPORT_CONFIRMATION_REQUEST = "Are you sure you wnat to proceed with importing removal settings?"\
                                          "\nWARNING: Any current settings will be lost."
    FILTERS_IMPORT = "Import Settings"
    FILTERS_IMPORT_TOOLTIP = "Import Custom Removal Settings from file"
    FILTERS_EXPORT = "Export Settings"
    FILTERS_EXPORT_TOOLTIP = "Export Custom Removal Settings to file"
    FILTERS_IMPORT_NLTK = "Import NLTK stopwords"
    FILTERS_IMPORT_NLTK_TOOLTIP = "Append nltk stop words to removal list"
    FILTERS_IMPORT_SPACY = "Import spaCy stopwords"
    FILTERS_IMPORT_SPACY_TOOLTIP = "Append spaCy stop words to removal list"

    FILTERS_REFRESH_BUSY_LABEL = "Refreshing Filter for Dataset: "
    FILTERS_REFRESH_BUSY_MSG = "Refreshing Filter for Dataset: "
    
    FILTERS_RELOAD_BUSY_LABEL = "Reloading Filter for Dataset: "
    FILTERS_RELOAD_BUSY_MSG = "Reloading Filter for Dataset: "

    FILTERS_DISPLAY_BUSY_LABEL = "Displaying Filter for Dataset: "
    FILTERS_DISPLAY_BUSY_MSG = "Displaying Filter for Dataset: "

    IMPACT_LABEL = "Impact on Dataset"


    LOAD_BUSY_MSG_CONFIG = "Loading Data Cleaning & Filtering Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Data Cleaning & Filtering Configurations"

    LOAD_FIELD_BUSY_MSG = "Loading field: "
    SAVE_FIELD_BUSY_MSG = "Saving field: "

class Sampling(Samples):
    SAMPLE_NAME = "Name of Sample:"

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

    NEW_CODE_NOTUNIQUE_ERROR = "New code has the same name as an existing code.\nCodes must have unique names."
    NEW_CODE_BLANK_ERROR = "New code name is blank.\nCodes must have a unique name."
    RENAME_CODE_NOTUNIQUE_ERROR = "Code's new name is the same name as an existing code.\nCodes must have unique names."
    RENAME_CODE_BLANK_ERROR = "Code's new name is blank.\nCodes must have unique names."

    QUOTATIONS = "Quotations"
    PARAPHRASES = "Paraphrases"

    CONFIRM_DELETE_QUOTATIONS = "Are you sure you want to delete selected quotations?"

    LOAD_BUSY_MSG_CONFIG = "Loading Coding Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Coding Configurations"

class Reviewing(Main):
    LOAD_BUSY_MSG_CONFIG = "Loading Reviewing Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Reviewing Configurations"

class Reporting(Main):
    LOAD_BUSY_MSG_CONFIG = "Loading Reporting Configurations"
    SAVE_BUSY_MSG_CONFIG ="Saving Reporting Configurations"