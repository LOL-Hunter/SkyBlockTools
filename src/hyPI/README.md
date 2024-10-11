Integrated API to access all needed data from external API's. \
IMPORTAINT: This reference is NOT complete yet! 

# hyPI reference
This API is used to get detailed information about hypixel recipes, prices, and other.
The API is split into three parts:

* hyPI.hypixelAPI
* hyPI.recipeAPI
* hyPI.skyCoflnetAPI

# hyPI.hypixelAPI

This part is used to get detailed prices of items.\
But only current prices. To use the API an API_KEY is required!\
Create one HERE: https://developer.hypixel.net/

### 1. import
```python
from hyPI.hypixelAPI import fileLoader, APILoader, HypixelBazaarParser, HypixelAuctionParser, HypixelItemParser
from hyPI.constants import BazaarItemID, AuctionItemID, HypixelAPIURL
```
### 2. Request Hypixel bazaar API
```python
try:
    parser = HypixelBazaarParser(
        APILoader(HypixelAPIURL.BAZAAR_URL, <apikey:str>, <playerName:str>)
    )
except APIConnectionError as e:
    pass
except NoAPIKeySetException as e:
    pass
```
Parse data from file.
```python
parser = HypixelBazaarParser(
    fileLoader("<path here>")
)
```
Use parser:
```python
prod = parser.getProducts() #-> returns list of "Products".
prod = parser.getProductByID(BazaarItemID.ENCHANTED_SLIME_BLOCK) #-> get "Products" by id
ids = parser.getProductIDs() #-> returns all product ids as string
datetimeObject = parser.getLastUpdated() # -> returns last updated as datetime object.

for prod in parser.getProducts(): #-> you can also iterate through products.
    pass

```
Use the product:
```python
prod.getInstaBuyPrice()  #-> returns insta buy price.
prod.getInstaSellPrice() #-> returns insta sell price.
prod.getBuyVolume()      #-> returns buy volume of given Item.
prod.getSellVolume()     #-> returns sell volume of given Item.
prod.getBuyOrdersTotal() #-> returns total buy orders.
prod.getSellOrdersTotal()#-> returns total sell orders.
list_ = prod.getInstaSellPriceList(5) #-> returns list of 5 (if available) items from the price stack (sum(list_) to get exact price for more than one item)
list_ = prod.getInstaBuyPriceList(5)  #-> returns list of 5 (if available) items from the price stack

orders = prod.getBuyOrders() #-> returns list of "Orders" that are placed on given item
orders = prod.getSellOrders() #-> returns list of "Orders" that are placed on given item
```
Use orders:
```python
order.getAmount()       #-> returns amount of items in current sell/buy order.
order.getPricePerUnit() #-> returns price per unit in current sell/buy order.
order.getOrders()       #-> returns amount of players set order with this specific price.
```
# Sky.Conflnet API reference
This API provides access to multiple histories to get the prices of items in the past.
### 1. import
```python
from hyPI.skyCoflnetAPI import SkyConflnetAPI
from hyPI.constants import BazaarItemID, AuctionItemID
```
### 2. Bazaar
#### 2.1 Get Bazaar price history
Get different histories in different timespans from different items. Pass ItemType as parameter.
```python
bz_hist = SkyConflnetAPI.getBazaarHistoryHour(BazaarItemID.SLIME_BALL)     #-> hourly item price history
bz_hist = SkyConflnetAPI.getBazaarHistoryDay(BazaarItemID.SLIME_BALL)      #-> daily item price history
bz_hist = SkyConflnetAPI.getBazaarHistoryWeek(BazaarItemID.SLIME_BALL)     #-> weekly item price history
bz_hist = SkyConflnetAPI.getBazaarHistoryComplete(BazaarItemID.SLIME_BALL) #-> entire item price history
```
The function returns a "BazaarHistory" instance with following methods:
```python
hist = bz_hist.getTimeSlots() #-> returns a list of BazaarHistoryProduct instances
hist = bz_hist[1] #-> also accessable though index.
hist = bz_hist.getTimeSlotAT(<timestamp>) #-> returns an instance of BazaarHistoryProduct at given timestamp
```
BazaarHistoryProduct has following methods:
```python
hist.getMaxBuyPrice()   #-> return max buy price of current item in current timespan
hist.getMinBuyPrice()   #-> return min buy price of current item in current timespan
hist.getMaxSellPrice()  #-> return max sell price of current item in current timespan
hist.getMinSellPrice()  #-> return min sell price of current item in current timespan

hist.getBuyPrice()      #-> returns buy price of current item at current timestamp
hist.getSellPrice()     #-> returns sell price of current item at current timestamp

hist.getSellVolume()    #-> returns volume at current timestamp
hist.getBuyVolume()     #-> returns volume at current timestamp

hist.getBuyMovingWeek() #-> returns how many items moved through buy in a Week
hist.getSellMovingWeek()#-> returns how many items moved through sell in a Week

hist.getTimestamp()     #-> returns timestamp of the data capture
```
#### 2.2 Get current Bazaar item data
Use this method to get the newest item data available.
```python
bz_data = SkyConflnetAPI.getBazaarItemPrice(BazaarItemID.ENCHANTED_SLIME_BLOCK)
```
```python
bz_data.getBuyPrice()      #-> returns newest buy price of current item
bz_data.getSellPrice()     #-> returns newest sell price of current item
bz_data.getAvailableItems()#-> returns newest available items in stock
bz_data.getTimestamp()     #-> returns timestamp of the data capture
```
### 3. Auction House data
#### 3.1 Get Auction House price history
Get different histories in different timespans from different items. Pass ItemType as parameter.
```python
ah_hist = SkyConflnetAPI.getAuctionHistoryDay(AuctionItemID.WISE_DRAGON_BOOTS)      #-> daily item price history
ah_hist = SkyConflnetAPI.getAuctionHistoryWeek(AuctionItemID.WISE_DRAGON_BOOTS)     #-> weekly item price history
ah_hist = SkyConflnetAPI.getAuctionHistoryMonth(AuctionItemID.WISE_DRAGON_BOOTS)    #-> monthly item price history
ah_hist = SkyConflnetAPI.getAuctionHistoryComplete(AuctionItemID.WISE_DRAGON_BOOTS) #-> entire item price history
```
The function returns a "AuctionHistory" instance with following methods:
```python
hist = ah_hist.getTimeSlots() #-> returns a list of AuctionHistoryProduct instances
hist = ah_hist[1] #-> also accessable though index.
hist = ah_hist.getTimeSlotAT(<timestamp>) #-> returns an instance of AuctionHistoryProduct at given timestamp
```
AuctionHistoryProduct has following methods:
```python
hist.getMaxBuyPrice()   #-> returns max buy price of current item in current timespan
hist.getMinBuyPrice()   #-> returns min buy price of current item in current timespan
hist.getAveragePrice()  #-> returns average price in current timespan

hist.getVolume()        #-> returns volume at current timestamp

hist.getTimestamp()     #-> returns timestamp of the data capture
```
#### 3.2 Get current Auction item data
Use this method to get the newest item data available.
```python
ah_data = SkyConflnetAPI.getAuctionItemPrice(AuctionItemID.WISE_DRAGON_BOOTS)
```


```python
ah_data.getBuyPrice()      #-> returns newest buy price of current item
ah_data.getSellPrice()     #-> returns newest sell price of current item
ah_data.getAvailableItems()#-> returns newest available items in stock
ah_data.getTimestamp()     #-> returns timestamp of the data capture
```
### 4. Get crafing Recipes
Get the Recipe from API.
```python
recipe = SkyConflnetAPI.getCraftingRecipe(AuctionItemID.WISE_DRAGON_BOOTS)
```
Use Recipe:
```python
pattern = recipe.getPattern() #-> get pattern
```
This returns a Dictionary. The keys in relation to the crafting field are shown here:

    A1 A2 A3
    B1 B2 B3
    C1 C2 C3
The Dictionary value is a Tuple with two values: ItemID and Amount
```python
ItemID(str)          Amount(int)
("WISE_DRAGON_BOOTS", 10)
```
If the slot is empty:
```python
(None, 0)
```
### 5. Mayor Data
Get Mayor Data from API:
```python
m_hist = SkyConflnetAPI.getMayorData()
```

```python
m_data = m_hist.getCurrentMayor() #-> returns "MayorData" instance on current active Mayor.
m_data = m_hist.getMayors() #-> returns a List of "MayorData" instance of all available Mayors in the past.
m_data = m_hist.getMayorAtYear(<year>) #-> returns "MayorData" instance of the given SkyBlock Year.
```
"MayorData" represents one Mayor.
It has the following methods.

```python
m_data._getID()  # -> returns an ID (not yes sure for what use)
m_data.getName()  # -> returns mayors name.
m_data.getKey()  # -> returns its type: for ex. ("fishing", "farming", ...)
m_data.getYear()  # -> returns the SkyBlock year this mayor is active.
m_data.getStartTimestamp()  # -> returns the timestamp when the mayor gets active.
m_data.getEndTimestamp()  # -> returns the timestamp when the mayor time is over.
m_data.getPerkAmount()  # -> returns how many perks the mayor has.
m_perks = m_data.getPerks()  # -> returns a list of mayors perks as "MayorPerk" ("explained below")
mayors = m_data.getElectionCandidates()  # -> returns get the Candidates. (Where this mayor won the election)
```

"mayors" is a list with "Mayor" instances.
This represents the candidates who list this election.
```python
mayors[0].getName()      #-> returns mayors name.
mayors[0].getKey()       #-> returns its type: for ex. ("fishing", "farming", ...)
m_perks = mayors[0].getPerks() #-> returns a list of mayors perks as "MayorPerk" ("explained below")
```

Use the "MayorPerks" interface:
"m_perks" is a List with "MayorPerks" instances.

```python
m_perks[0].getDescription() #-> returns perk description
m_perks[0].getPerkName()    #-> returns perk name
```
