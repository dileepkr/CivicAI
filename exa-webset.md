# Create a Webset

> Creates a new Webset with optional search, import, and enrichment configurations. The Webset will automatically begin processing once created.

You can specify an `externalId` to reference the Webset with your own identifiers for easier integration.

## OpenAPI

````yaml post /v0/websets
paths:
  path: /v0/websets
  method: post
  servers:
    - url: https://api.exa.ai/websets/
      description: Production
  request:
    security:
      - title: api key
        parameters:
          query: {}
          header:
            x-api-key:
              type: apiKey
              description: Your Exa API key
          cookie: {}
    parameters:
      path: {}
      query: {}
      header: {}
      cookie: {}
    body:
      application/json:
        schemaArray:
          - type: object
            properties:
              search:
                allOf:
                  - type:
                      - object
                    properties:
                      query:
                        type:
                          - string
                        minLength: 1
                        maxLength: 5000
                        description: >-
                          Natural language search query describing what you are
                          looking for.


                          Be specific and descriptive about your requirements,
                          characteristics, and any constraints that help narrow
                          down the results.


                          Any URLs provided will be crawled and used as
                          additional context for the search.
                        examples:
                          - >-
                            Marketing agencies based in the US, that focus on
                            consumer products.
                          - >-
                            AI startups in Europe that raised Series A funding
                            in 2024
                          - >-
                            SaaS companies with 50-200 employees in the fintech
                            space
                      count:
                        default: 10
                        type:
                          - number
                        minimum: 1
                        description: >-
                          Number of Items the Webset will attempt to find.


                          The actual number of Items found may be less than this
                          number depending on the search complexity.
                      entity:
                        $ref: '#/components/schemas/Entity'
                        description: >-
                          Entity the Webset will return results for.


                          It is not required to provide it, we automatically
                          detect the entity from all the information provided in
                          the query. Only use this when you need more fine
                          control.
                      criteria:
                        type:
                          - array
                        items:
                          type:
                            - object
                          $ref: '#/components/schemas/CreateCriterionParameters'
                          title: CreateCriterionParameters
                        minItems: 1
                        maxItems: 5
                        description: >-
                          Criteria every item is evaluated against.


                          It's not required to provide your own criteria, we
                          automatically detect the criteria from all the
                          information provided in the query. Only use this when
                          you need more fine control.
                      recall:
                        type:
                          - boolean
                        description: >-
                          Whether to provide an estimate of how many total
                          relevant results could exist for this search.

                          Result of the analysis will be available in the
                          `recall` field within the search request.
                      exclude:
                        type:
                          - array
                        items:
                          type:
                            - object
                          properties:
                            source:
                              type:
                                - string
                              enum:
                                - import
                                - webset
                            id:
                              type:
                                - string
                              minLength: 1
                              description: The ID of the source to exclude.
                          required:
                            - source
                            - id
                        description: >-
                          Sources (existing imports or websets) to exclude from
                          search results. Any results found within these sources
                          will be omitted to prevent finding them during search.
                    required:
                      - query
                    description: Create initial search for the Webset.
              import:
                allOf:
                  - type:
                      - array
                    items:
                      type:
                        - object
                      properties:
                        source:
                          type:
                            - string
                          enum:
                            - import
                            - webset
                        id:
                          type:
                            - string
                          minLength: 1
                          description: The ID of the source to search.
                      required:
                        - source
                        - id
                    description: >-
                      Import data from existing Websets and Imports into this
                      Webset.
              enrichments:
                allOf:
                  - type:
                      - array
                    items:
                      type:
                        - object
                      $ref: '#/components/schemas/CreateEnrichmentParameters'
                      title: CreateEnrichmentParameters
                    description: >-
                      Add enrichments to extract additional data from found
                      items.


                      Enrichments automatically search for and extract specific
                      information (like contact details, funding data, employee
                      counts, etc.) from each item added to your Webset.
              externalId:
                allOf:
                  - type:
                      - string
                    maxLength: 300
                    description: >-
                      The external identifier for the webset.


                      You can use this to reference the Webset by your own
                      internal identifiers.
              metadata:
                allOf:
                  - description: >-
                      Set of key-value pairs you want to associate with this
                      object.
                    type:
                      - object
                    additionalProperties:
                      type:
                        - string
                      maxLength: 1000
            required: true
            refIdentifier: '#/components/schemas/CreateWebsetParameters'
            examples:
              - search: &ref_0
                  query: >-
                    Marketing agencies based in the US, that focus on consumer
                    products.
                  count: 10
            example:
              search: *ref_0
        examples:
          example:
            value:
              search:
                query: >-
                  Marketing agencies based in the US, that focus on consumer
                  products.
                count: 10
    codeSamples:
      - label: JavaScript
        lang: javascript
        source: |-
          // npm install exa-js
          import Exa from 'exa-js';
          const exa = new Exa('YOUR_EXA_API_KEY');

          const webset = await exa.websets.create({
            search: {
              query: "Tech companies in San Francisco",
              count: 10
            }
          });

          console.log(`Created webset: ${webset.id}`);
      - label: Python
        lang: python
        source: |-
          # pip install exa-py
          from exa_py import Exa
          exa = Exa('YOUR_EXA_API_KEY')

          webset = exa.websets.create(params={
              'search': {
                  'query': 'Tech companies in San Francisco',
                  'count': 10
              }
          })

          print(f'Created webset: {webset.id}')
  response:
    '201':
      application/json:
        schemaArray:
          - type: object
            properties:
              id:
                allOf:
                  - type:
                      - string
                    description: The unique identifier for the webset
              object:
                allOf:
                  - type: string
                    const: webset
                    default: webset
              status:
                allOf:
                  - type:
                      - string
                    enum:
                      - idle
                      - running
                      - paused
                    description: The status of the webset
                    title: WebsetStatus
              externalId:
                allOf:
                  - type: string
                    description: The external identifier for the webset
                    nullable: true
              title:
                allOf:
                  - type: string
                    description: The title of the webset
                    nullable: true
              searches:
                allOf:
                  - type:
                      - array
                    items:
                      type:
                        - object
                      $ref: '#/components/schemas/WebsetSearch'
                    description: The searches that have been performed on the webset.
              imports:
                allOf:
                  - type:
                      - array
                    items:
                      type:
                        - object
                      $ref: '#/components/schemas/Import'
                    description: Imports that have been performed on the webset.
              enrichments:
                allOf:
                  - type:
                      - array
                    items:
                      type:
                        - object
                      $ref: '#/components/schemas/WebsetEnrichment'
                    description: The Enrichments to apply to the Webset Items.
              monitors:
                allOf:
                  - type:
                      - array
                    items:
                      type:
                        - object
                      $ref: '#/components/schemas/Monitor'
                    description: The Monitors for the Webset.
              streams:
                allOf:
                  - type:
                      - array
                    items: {}
                    description: The Streams for the Webset.
              metadata:
                allOf:
                  - default: {}
                    description: >-
                      Set of key-value pairs you want to associate with this
                      object.
                    type:
                      - object
                    additionalProperties:
                      type:
                        - string
                      maxLength: 1000
              createdAt:
                allOf:
                  - type:
                      - string
                    format: date-time
                    description: The date and time the webset was created
              updatedAt:
                allOf:
                  - type:
                      - string
                    format: date-time
                    description: The date and time the webset was updated
            refIdentifier: '#/components/schemas/Webset'
            requiredProperties:
              - id
              - object
              - status
              - externalId
              - title
              - searches
              - imports
              - enrichments
              - monitors
              - streams
              - createdAt
              - updatedAt
        examples:
          example:
            value:
              id: <string>
              object: webset
              status: idle
              externalId: <string>
              title: <string>
              searches:
                - id: <string>
                  object: webset_search
                  status: created
                  query: <string>
                  entity:
                    type: company
                  criteria:
                    - description: <string>
                      successRate: 50
                  count: 2
                  behavior: override
                  exclude:
                    - source: import
                      id: <string>
                  progress:
                    found: 123
                    analyzed: 123
                    completion: 50
                    timeLeft: 123
                  recall:
                    expected:
                      total: 123
                      confidence: high
                      bounds:
                        min: 123
                        max: 123
                    reasoning: <string>
                  metadata: {}
                  canceledAt: '2023-11-07T05:31:56Z'
                  canceledReason: webset_deleted
                  createdAt: '2023-11-07T05:31:56Z'
                  updatedAt: '2023-11-07T05:31:56Z'
              imports:
                - id: <string>
                  object: import
                  status: pending
                  format: csv
                  entity:
                    type: <string>
                  title: <string>
                  count: 123
                  metadata: {}
                  failedReason: invalid_format
                  failedAt: '2023-11-07T05:31:56Z'
                  failedMessage: <string>
                  createdAt: '2023-11-07T05:31:56Z'
                  updatedAt: '2023-11-07T05:31:56Z'
              enrichments:
                - id: <string>
                  object: webset_enrichment
                  status: pending
                  websetId: <string>
                  title: <string>
                  description: <string>
                  format: text
                  options:
                    - label: <string>
                  instructions: <string>
                  metadata: {}
                  createdAt: '2023-11-07T05:31:56Z'
                  updatedAt: '2023-11-07T05:31:56Z'
              monitors:
                - id: <string>
                  object: monitor
                  status: enabled
                  websetId: <string>
                  cadence:
                    cron: <string>
                    timezone: Etc/UTC
                  behavior:
                    type: search
                    config:
                      query: <string>
                      criteria:
                        - description: <string>
                      entity:
                        type: <string>
                      count: 123
                      behavior: append
                  lastRun:
                    id: <string>
                    object: monitor_run
                    status: created
                    monitorId: <string>
                    type: search
                    completedAt: '2023-11-07T05:31:56Z'
                    failedAt: '2023-11-07T05:31:56Z'
                    failedReason: <string>
                    canceledAt: '2023-11-07T05:31:56Z'
                    createdAt: '2023-11-07T05:31:56Z'
                    updatedAt: '2023-11-07T05:31:56Z'
                  nextRunAt: '2023-11-07T05:31:56Z'
                  metadata: {}
                  createdAt: '2023-11-07T05:31:56Z'
                  updatedAt: '2023-11-07T05:31:56Z'
              streams:
                - <any>
              metadata: {}
              createdAt: '2023-11-07T05:31:56Z'
              updatedAt: '2023-11-07T05:31:56Z'
        description: Webset created
    '409':
      _mintlify/placeholder:
        schemaArray:
          - type: any
            description: Webset with this externalId already exists
        examples: {}
        description: Webset with this externalId already exists
  deprecated: false
  type: path
components:
  schemas:
    CompanyEntity:
      type:
        - object
      properties:
        type:
          type: string
          const: company
          default: company
      required:
        - type
      title: Company
    PersonEntity:
      type:
        - object
      properties:
        type:
          type: string
          const: person
          default: person
      required:
        - type
      title: Person
    ArticleEntity:
      type:
        - object
      properties:
        type:
          type: string
          const: article
          default: article
      required:
        - type
      title: Article
    ResearchPaperEntity:
      type:
        - object
      properties:
        type:
          type: string
          const: research_paper
          default: research_paper
      required:
        - type
      title: Research Paper
    CustomEntity:
      type:
        - object
      properties:
        type:
          type: string
          const: custom
          default: custom
        description:
          type:
            - string
          minLength: 2
          maxLength: 200
      required:
        - type
        - description
      title: Custom
    Entity:
      oneOf:
        - type:
            - object
          $ref: '#/components/schemas/CompanyEntity'
        - type:
            - object
          $ref: '#/components/schemas/PersonEntity'
        - type:
            - object
          $ref: '#/components/schemas/ArticleEntity'
        - type:
            - object
          $ref: '#/components/schemas/ResearchPaperEntity'
        - type:
            - object
          $ref: '#/components/schemas/CustomEntity'
    CreateCriterionParameters:
      type:
        - object
      properties:
        description:
          type:
            - string
          minLength: 1
          maxLength: 1000
          description: The description of the criterion
      required:
        - description
    CreateEnrichmentParameters:
      type:
        - object
      properties:
        description:
          type:
            - string
          minLength: 1
          maxLength: 5000
          description: >-
            Provide a description of the enrichment task you want to perform to
            each Webset Item.
        format:
          type:
            - string
          enum:
            - text
            - date
            - number
            - options
            - email
            - phone
          description: >-
            Format of the enrichment response.


            We automatically select the best format based on the description. If
            you want to explicitly specify the format, you can do so here.
        options:
          type:
            - array
          items:
            type:
              - object
            properties:
              label:
                type:
                  - string
                description: The label of the option
            required:
              - label
          minItems: 1
          maxItems: 150
          description: >-
            When the format is options, the different options for the enrichment
            agent to choose from.
        metadata:
          description: Set of key-value pairs you want to associate with this object.
          type:
            - object
          additionalProperties:
            type:
              - string
            maxLength: 1000
      required:
        - description
    WebsetSearch:
      type:
        - object
      properties:
        id:
          type:
            - string
          description: The unique identifier for the search
        object:
          type: string
          const: webset_search
          default: webset_search
        status:
          type:
            - string
          enum:
            - created
            - running
            - completed
            - canceled
          description: The status of the search
          title: WebsetSearchStatus
        query:
          type:
            - string
          minLength: 1
          maxLength: 5000
          description: The query used to create the search.
        entity:
          $ref: '#/components/schemas/Entity'
          description: >-
            The entity the search will return results for.


            When no entity is provided during creation, we will automatically
            select the best entity based on the query.
          nullable: true
        criteria:
          type:
            - array
          items:
            type:
              - object
            properties:
              description:
                type:
                  - string
                minLength: 1
                maxLength: 1000
                description: The description of the criterion
              successRate:
                type:
                  - number
                minimum: 0
                maximum: 100
                description: >-
                  Value between 0 and 100 representing the percentage of results
                  that meet the criterion.
            required:
              - description
              - successRate
          description: >-
            The criteria the search will use to evaluate the results. If not
            provided, we will automatically generate them for you.
        count:
          type:
            - number
          minimum: 1
          description: >-
            The number of results the search will attempt to find. The actual
            number of results may be less than this number depending on the
            search complexity.
        behavior:
          default: override
          type:
            - string
          $ref: '#/components/schemas/WebsetSearchBehavior'
          description: >-
            The behavior of the search when it is added to a Webset.


            - `override`: the search will replace the existing Items found in
            the Webset and evaluate them against the new criteria. Any Items
            that don't match the new criteria will be discarded.

            - `append`: the search will add the new Items found to the existing
            Webset. Any Items that don't match the new criteria will be
            discarded.
        exclude:
          type:
            - array
          items:
            type:
              - object
            properties:
              source:
                type:
                  - string
                enum:
                  - import
                  - webset
              id:
                type:
                  - string
            required:
              - source
              - id
          description: >-
            Sources (existing imports or websets) used to omit certain results
            to be found during the search.
        progress:
          type:
            - object
          properties:
            found:
              type:
                - number
              description: The number of results found so far
            analyzed:
              type:
                - number
              description: The number of results analyzed so far
            completion:
              type:
                - number
              minimum: 0
              maximum: 100
              description: The completion percentage of the search
            timeLeft:
              type: number
              description: The estimated time remaining in seconds, null if unknown
              nullable: true
          required:
            - found
            - analyzed
            - completion
            - timeLeft
          description: The progress of the search
        recall:
          type: object
          properties:
            expected:
              type:
                - object
              properties:
                total:
                  type:
                    - number
                  description: The estimated total number of potential matches
                confidence:
                  type:
                    - string
                  enum:
                    - high
                    - medium
                    - low
                  description: The confidence in the estimate
                bounds:
                  type:
                    - object
                  properties:
                    min:
                      type:
                        - number
                      description: The minimum estimated total number of potential matches
                    max:
                      type:
                        - number
                      description: The maximum estimated total number of potential matches
                  required:
                    - min
                    - max
              required:
                - total
                - confidence
                - bounds
            reasoning:
              type:
                - string
              description: The reasoning for the estimate
          required:
            - expected
            - reasoning
          description: >-
            Recall metrics for the search, null if not yet computed or
            requested.
          nullable: true
        metadata:
          default: {}
          description: Set of key-value pairs you want to associate with this object.
          type:
            - object
          additionalProperties:
            type:
              - string
            maxLength: 1000
        canceledAt:
          type: string
          format: date-time
          description: The date and time the search was canceled
          nullable: true
        canceledReason:
          type: string
          $ref: '#/components/schemas/WebsetSearchCanceledReason'
          description: The reason the search was canceled
          nullable: true
        createdAt:
          type:
            - string
          format: date-time
          description: The date and time the search was created
        updatedAt:
          type:
            - string
          format: date-time
          description: The date and time the search was updated
      required:
        - id
        - object
        - status
        - query
        - entity
        - criteria
        - count
        - exclude
        - progress
        - recall
        - canceledAt
        - canceledReason
        - createdAt
        - updatedAt
    Import:
      type:
        - object
      properties:
        id:
          type:
            - string
          description: The unique identifier for the Import
        object:
          type:
            - string
          enum:
            - import
          description: The type of object
        status:
          type:
            - string
          enum:
            - pending
            - processing
            - completed
            - failed
          description: The status of the Import
        format:
          type:
            - string
          enum:
            - csv
            - webset
          description: The format of the import.
        entity:
          $ref: '#/components/schemas/Entity'
          description: The type of entity the import contains.
          nullable: true
        title:
          type:
            - string
          description: The title of the import
        count:
          type:
            - number
          description: The number of entities in the import
        metadata:
          description: Set of key-value pairs you want to associate with this object.
          type:
            - object
          additionalProperties:
            type:
              - string
            maxLength: 1000
        failedReason:
          type: string
          enum:
            - invalid_format
            - invalid_file_content
            - missing_identifier
          description: The reason the import failed
          nullable: true
        failedAt:
          type: string
          format: date-time
          description: When the import failed
          nullable: true
        failedMessage:
          type: string
          description: A human readable message of the import failure
          nullable: true
        createdAt:
          type:
            - string
          format: date-time
          description: When the import was created
        updatedAt:
          type:
            - string
          format: date-time
          description: When the import was last updated
      required:
        - id
        - object
        - status
        - format
        - entity
        - title
        - count
        - metadata
        - failedReason
        - failedAt
        - failedMessage
        - createdAt
        - updatedAt
    WebsetEnrichment:
      type:
        - object
      properties:
        id:
          type:
            - string
          description: The unique identifier for the enrichment
        object:
          type: string
          const: webset_enrichment
          default: webset_enrichment
        status:
          type:
            - string
          enum:
            - pending
            - canceled
            - completed
          description: The status of the enrichment
          title: WebsetEnrichmentStatus
        websetId:
          type:
            - string
          description: The unique identifier for the Webset this enrichment belongs to.
        title:
          type: string
          description: >-
            The title of the enrichment.


            This will be automatically generated based on the description and
            format.
          nullable: true
        description:
          type:
            - string
          description: >-
            The description of the enrichment task provided during the creation
            of the enrichment.
        format:
          type: string
          $ref: '#/components/schemas/WebsetEnrichmentFormat'
          description: The format of the enrichment response.
          nullable: true
        options:
          type: array
          items:
            type:
              - object
            properties:
              label:
                type:
                  - string
                description: The label of the option
            required:
              - label
          description: >-
            When the format is options, the different options for the enrichment
            agent to choose from.
          title: WebsetEnrichmentOptions
          nullable: true
        instructions:
          type: string
          description: >-
            The instructions for the enrichment Agent.


            This will be automatically generated based on the description and
            format.
          nullable: true
        metadata:
          default: {}
          description: The metadata of the enrichment
          type:
            - object
          additionalProperties:
            type:
              - string
            maxLength: 1000
        createdAt:
          type:
            - string
          format: date-time
          description: The date and time the enrichment was created
        updatedAt:
          type:
            - string
          format: date-time
          description: The date and time the enrichment was updated
      required:
        - id
        - object
        - status
        - websetId
        - title
        - description
        - format
        - options
        - instructions
        - createdAt
        - updatedAt
    MonitorRun:
      type:
        - object
      properties:
        id:
          type:
            - string
          description: The unique identifier for the Monitor Run
        object:
          type:
            - string
          enum:
            - monitor_run
          description: The type of object
        status:
          type:
            - string
          enum:
            - created
            - running
            - completed
            - canceled
            - failed
          description: The status of the Monitor Run
        monitorId:
          type:
            - string
          description: The monitor that the run is associated with
        type:
          type:
            - string
          enum:
            - search
            - refresh
          description: The type of the Monitor Run
        completedAt:
          type: string
          format: date-time
          description: When the run completed
          nullable: true
        failedAt:
          type: string
          format: date-time
          description: When the run failed
          nullable: true
        failedReason:
          type: string
          description: The reason the run failed
          nullable: true
        canceledAt:
          type: string
          format: date-time
          description: When the run was canceled
          nullable: true
        createdAt:
          type:
            - string
          format: date-time
          description: When the run was created
        updatedAt:
          type:
            - string
          format: date-time
          description: When the run was last updated
      required:
        - id
        - object
        - monitorId
        - status
        - type
        - completedAt
        - failedAt
        - failedReason
        - canceledAt
        - createdAt
        - updatedAt
    Monitor:
      type:
        - object
      properties:
        id:
          type:
            - string
          description: The unique identifier for the Monitor
        object:
          type:
            - string
          enum:
            - monitor
          description: The type of object
        status:
          type:
            - string
          enum:
            - enabled
            - disabled
          description: The status of the Monitor
        websetId:
          type:
            - string
          description: The id of the Webset the Monitor belongs to
        cadence:
          type:
            - object
          properties:
            cron:
              description: >-
                Cron expression for monitor cadence (must be a valid Unix cron
                with 5 fields). The schedule must trigger at most once per day.
              type:
                - string
            timezone:
              description: IANA timezone (e.g., "America/New_York")
              default: Etc/UTC
              type:
                - string
          required:
            - cron
          description: How often the monitor will run
        behavior:
          type:
            - object
          properties:
            type:
              type: string
              const: search
              default: search
            config:
              type:
                - object
              properties:
                query:
                  type:
                    - string
                  minLength: 2
                  maxLength: 10000
                  description: >-
                    The query to search for. By default, the query from the last
                    search is used.
                criteria:
                  type:
                    - array
                  items:
                    type:
                      - object
                    properties:
                      description:
                        type:
                          - string
                        minLength: 2
                        maxLength: 1000
                    required:
                      - description
                  maxItems: 5
                  description: >-
                    The criteria to search for. By default, the criteria from
                    the last search is used.
                entity:
                  $ref: '#/components/schemas/Entity'
                  title: Entity
                  description: >-
                    The entity to search for. By default, the entity from the
                    last search/import is used.
                count:
                  type:
                    - number
                  exclusiveMinimum: 0
                  description: The maximum number of results to find
                behavior:
                  default: append
                  type:
                    - string
                  enum:
                    - override
                    - append
                  description: The behaviour of the Search when it is added to a Webset.
              required:
                - count
              description: >-
                Specify the search parameters for the Monitor.


                By default, the search parameters (query, entity and criteria)
                from the last search are used when no parameters are provided.
          required:
            - type
            - config
          description: Behavior to perform when monitor runs
        lastRun:
          type: object
          $ref: '#/components/schemas/MonitorRun'
          title: MonitorRun
          description: The last run of the monitor
          nullable: true
        nextRunAt:
          type: string
          format: date-time
          description: Date and time when the next run will occur in
          nullable: true
        metadata:
          description: Set of key-value pairs you want to associate with this object.
          type:
            - object
          additionalProperties:
            type:
              - string
            maxLength: 1000
        createdAt:
          type:
            - string
          format: date-time
          description: When the monitor was created
        updatedAt:
          type:
            - string
          format: date-time
          description: When the monitor was last updated
      required:
        - id
        - object
        - status
        - websetId
        - cadence
        - behavior
        - lastRun
        - nextRunAt
        - metadata
        - createdAt
        - updatedAt
    WebsetEnrichmentFormat:
      type: string
      enum:
        - text
        - date
        - number
        - options
        - email
        - phone
    WebsetSearchBehavior:
      type: string
      enum:
        - override
        - append
    WebsetSearchCanceledReason:
      type: string
      enum:
        - webset_deleted
        - webset_canceled

````