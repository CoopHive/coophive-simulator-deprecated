# coophive design doc

## context

The rules of players in the simulated world are:

 * you must correctly report your wallet address (we're not actually doing cryptography in the simulator)
 * we're ignoring gas
 * we MUST include a TX object with the correct address and value (which can be 0) in every tx call

## services

Services:

 * smart contract
 * resource provider (RP)
 * job creator (JC)
 * solver
 * mediator
 * directory

## types

These types are global data structures:

#### Range

Represents a range of values

 * min `uint`
 * max `uint`

#### Machine

The ID of the machine is the IPFS cid of the JSON document with the following structure.

Represents a hardware vm or other such machine that resource offers are made from.

This is read-only metadata used to inform the market place of the actual topology of the network.

This enables resource providers to advertise machine capacity without having to constantly post resource offers.
 
 * owner `address`
 * created `uint` UTC time stamp the machine was created
 * timeout `uint` the number of seconds since the created date the machine is no longer valid
 * CPU `uint`
 * GPU `uint`
 * RAM `uint`
 * labels `map[string]string`

TODO: do we need fractional CPU values like 0.5?

#### ResourceOffer (RO)

The ID of the resource offer is the IPFS cid of the JSON document with the following structure.
 
 * owner `address`
 * target `address` (can be null - the job creator this offer is for)
 * created `uint` UTC time stamp the resource offer was created
 * timeout `uint` the number of seconds since the created date the resource offer is no longer valid
 * CPU `uint`
 * GPU `uint`
 * RAM `uint`
 * prices `map[string]uint`
   * this is price per instruction for each module
  
#### JobOffer (JO)

The ID of the job offer is the IPFS cid of the JSON document with the following structure.

 * owner `address`
 * target `address` (can be null - the resource provider this offer is for)
 * CPU `Range`
 * GPU `Range`
 * RAM `Range`
 * module `string`
 * price `uint`
   * this is price per instruction

#### Deal

The agreement of a RP and JC for a RO and JO

 * resourceProvider `address`
 * jobCreator `address`
 * resourceOffer `CID`
 * jobOffer `CID`
 * timeout `uint`
 * timeoutDeposit `uint`
 * jobDeposit `uint`
 * resultsMultiple `uint`
 
## identity

All services will have a `PRIVATE_KEY` used to sign messages.

It should be easy to derive an `address` from that private key that we can use as an identity.

We will use the same private key and address across both smart contract and non smart contract RPC calls.

Each of the services making and accepting api requests from other services must use the private key to sign and identify requests.

The simulator doesn't need to do actual crypto but it must use the concept of `an address signed this` to authenticate and authorise requests.

## IPFS, CIDs and directory service

There are various mentions of CIDs throughout this document - e.g. the Job Offers, Resource Offers and Deals are communicated with the smart contract only using their IPFS CID.

So, any service that interacts with the smart contract must be able to write and resolve CIDs to and from IPFS.

In the case of the results - we need to ensure the results were available to the job creator to ensure they cannot claim they could not download the results.

For this reason, we use a `directory` service that is used to store the results by the resource provider and confirm availability to the job creator.

The directory service will use the same CID to identify content and will utilize IPFS to store the content and distribute it to the rest of the IPFS network.

Job creators and resource providers can list their trusted directory services - if the config is not provided, it will use the default option registered on the contract (i.e. the default services run by us).

For a match to occur - both sides must have an overlap in their trusted directory services.

Nodes can run their own directory services and call `registerServiceProvider` and any other node can change which directory services they trust.

TODO: how do directory serices get paid? (is this v2 protocol?)

## solver

The service that matches resource offers and job offers.

The solver will eventually be removed in favour of point to point communication.

For that reason - the solver has 2 distinct sides to it's api, the resource provider side and job creator side.

The resource provider and job creator will have their **own** api's - seperate to these that their respective CLI's will use.

Job creators and resource providers can be configured to point at a different solver - if the config is not provided, it will use the default option registered on the contract (i.e. the default services run by us).

The match happens on the solver so the resource provider and job creator must be pointing at the same solver for matches to be made.

The default solver service will be run by us, other nodes can run their own directory services and call `registerServiceProvider`

#### solver stages

It should be possible for nodes to publish their offers to multiple solvers (as in advertise in multiple marketplaces).  However, the solver will be replaced by a libp2p transport in the future and so is a stop-gap and not worth.

 * stage 1 = solver matches, but with marketplace of solvers
   * single process solver service
   * job creator and resource provider api's are merged
 * state 2 = solver runs autonomous agents on behalf of nodes
   * single process solver service
   * job creator and resource provider api's are split
 * stage 3 = autonomous agents are run locally and solver is used for transporting messages
   * solver is now dumb transport
   * resource provider and job creator apis are now edge services
   * the solver only connects messages
 * stage 4 = solver is totally removed, nodes communicate via libp2p
   * there is now no solver
   * libp2p replaces the solver transport

## meditor

The service that re-runs jobs to check what happened.

Job creators and resource providers can list their trusted mediators - if the config is not provided, it will use the default option registered on the contract (i.e. the default services run by us).

For a match to occur - both sides must have an overlap in their trusted mediators.

Nodes can run their own mediator services and call `registerServiceProvider` and any other node can change which mediator services they trust.

## smart contract

#### types

 * `type CID` - bytes32

 * `type ServiceType` - enum
    * resourceProvider
    * jobCreator
    * solver
    * mediator
    * directory

#### service provider discovery

 * `registerServiceProvider(serviceType, url, metadata)`
    * serviceType `ServiceType`
    * ID = msg._sender
    * url `string`
      * this is the advertised network URL, used by directory and solver
    * metadata `CID`

 * `setDefaultServiceProvider(serviceType, ID)` (admin)
    * register the given service provider as a default
 * `unsetDefaultServiceProvider(serviceType, ID)` (admin)
    * un-register the given service provider as a default

 * `unregisterServiceProvider(serviceType)`
    * serviceType `ServiceType`
    * ID = msg._sender

 * `listServiceProviders(serviceType) returns []address`
    * serviceType `ServiceType`
    * returns an array of IDs for the given service type

 * `getServiceProvider(serviceType, ID) returns (url, metadata, isDefault)`
    * serviceType `ServiceType`
    * ID `address`
    * url `string`
    * metadata `CID`
    * isDefault `bool`
      * is this service provider a default
    * return the URL and metadata CID for the given service provider

#### deals

 * `agreeMatch(party, dealID, directoryService, mediatorService, timeout, resultsMultiple, timeoutDeposit, jobDeposit)`
   * for the deal to be valid - the second party to agree MUST match exactly the same values as the first
   * party `ServiceType` - this must be either resourceProvider or jobCreator
   * dealID `CID`
   * directoryService `address`
     * the mutually agreed directory service used to transport specs and results
   * mediatorService `address`
     * the mutually agreed mediator service used to mediate results
   * timeout `uint`
     * the agreed upper bounds of time this job can take - TODO: is this in seconds or blocks?
   * resultsMultiple `uint`
     * the agreed multiple of the fee the resource provider will post when submitting results
   * timeoutDeposit `uint`
     * the agreed amount of deposit that will be lost if the job takes longer than timeout
     * if ServiceType == 'resourceProvider' this must equal msg._value
   * jobDeposit `uint`
     * the amount of deposit that will be lost if the job creator does not submit results
     * if ServiceType == 'jobCreator' this must equal msg._value

 * `getDeal(ID) returns (Deal)`
   
 * `submitResults(dealID, resultsCID, instructionCount, resultsDeposit)`
    * dealID `CID`
    * resultsCID `CID`
    * instructionCount `uint`
    * resultsDeposit `uint` (msg._value)
    * submit the results of the job to the smart contract

#### events

 * `ServiceProviderRegistered(serviceType, ID, url, metadata)`
   * serviceType `ServiceType`
   * ID = msg._sender
   * url `string`
     * this is the advertised network URL, used by directory and solver
   * metadata `CID`

 * `ServiceProviderUnregistered(serviceType, ID)`
   * serviceType `ServiceType`
   * ID = msg._sender
  
 * `MatchAgreed(party, dealID, directoryService, mediatorService, timeout, resultsMultiple, timeoutDeposit, jobDeposit)`
   * party `ServiceType`
   * dealID `CID`
   * directoryService `address`
   * mediatorService `address`
   * timeout `uint`
   * resultsMultiple `uint`
   * timeoutDeposit `uint`
   * jobDeposit `uint`

 * `DealAgreed(dealID)`
   * dealID `CID`
   * is called once both parties have called `MatchAgreed`
   * can then use `getDeal(ID)` to get details of deal

## solver

The following api's are what the resource provider and job creator will use to communicate with the solver.

Each API method will have access to a `TX` object that contains the address of the client.

#### resource provider

 * `createMachine(machineID, machine)`
   * machineID `CID`
   * machine `Machine`
   * list all machines for the resource provider

 * `createResourceOffer(resourceOfferID, resourceOffer, target)`
   * resourceOfferID `CID`
   * resourceOffer `ResourceOffer`
   * target `address` (can be zero)
   * tell parties connected to this solver about the resource offer
     * if `target` is specified - only tell the job creator with that address

 * `cancelResourceOffer(resourceOfferID)`
   * resourceOfferID `CID`
   * cancel the resource offer for everyone
   * this should be called once a match is seen

 * `resetResourceProvider()`
   * reset the resource provider state based on the tx passed in

#### resource provider autonomous agent

 * pro-active
   * always post new resource offers of a configured arrangement
   * possibly over-subscribe offers
   * agree any match
   * don't over-subscribe active deals
 * passive
   * wait for job offers that match
   * only post resource offer in response
   * agree any match
   * don't over-subscribe active deals

#### job creator

 * `createJobOffer(jobOfferID, jobOffer, target)`
   * resourceOfferID `CID`
   * jobOffer `JobOffer`
   * target `address` (can be zero)
   * tell parties connected to this solver about the job offer
     * if `target` is specified - only tell the resource provider with that address

 * `cancelJobOffer(jobOfferID)`
   * jobOfferID `CID`
   * cancel the job offer for everyone
   * this should be called once a match is seen

 * `resetJobCreator()`
   * reset the job creator state based on the tx passed in

#### job creator autonomous agent

Keep track of jobs in flight and use a random chance to decide if to challenge - i.e. the bus ticket method.

#### both

Methods called by both sides - all methods are context aware i.e. only return targeted offers for that address.

 * `listMachines(query) returns []Machine`
   * query `map[string]string`
     * `owner` = the address of the resource provider
   * returns an array of machines registered with this solver matching the query

 * `listResourceOffers() returns []ResourceOffer`
   * returns an array of resourceOffers that the msg._sender can see
   * this means resource offers that have been broadcast to everyone AND ones that have been sent to the msg._sender directly

 * `getResourceOffer(resourceOfferID) returns ResourceOffer`
   * throw error if msg._sender cannot see the resource offer
   * this means resource offers that have been broadcast to everyone AND ones that have been sent to the msg._sender directly

 * `listJobOffers() returns []JobOffer`
   * returns an array of jobOfferID's that the msg._sender can see
   * this means job offers that have been broadcast to everyone AND ones that have been sent to the msg._sender directly

 * `getJobOffer(jobOfferID) returns JobOffer`
   * throw error if msg._sender cannot see the job offer
   * this means resource offers that have been broadcast to everyone AND ones that have been sent to the msg._sender directly

#### events

Global resource/job offers are broadcast to everyone
Targeted resource/job offers only sent to the target subscriber

 * `onResourceOfferCreated(handler)`
   * handler `function(resourceOfferID, ResourceOffer)`
   * called when new resource offers are seen
   
 * `onResourceOfferCancelled(handler)`
   * handler `function(resourceOfferID, ResourceOffer)`
   * called when resource offers are cancelled

 * `onJobOfferCreated(handler)`
   * handler `function(jobOfferID, JobOffer)`
   * called when new job offers (either global or targeted) are seen

 * `onJobOfferCancelled(handler)`
   * handler `function(jobOfferID, JobOffer)`
   * called when job offers are cancelled

 * `onMatch(handler)`
   * handler `function(jobOfferID, resourceOfferID)`
   * called when new matches are made

## resource provider

The resource provider will connect to a solver and create resource offers.

It will connect to the solver by listing solvers from the smart contract and then using one (or more) to create resource offers and agree to matches.

#### config

Things we configure the resource provider with:

 * private key
 * metadata CID
 * machine id
 * machine spec
 * directory addresses
 * mediator addresses
 * solver address
