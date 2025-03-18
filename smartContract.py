import smartpy as sp

@sp.module
def main():

  class SmartContract(sp.Contract):

    def __init__(self, init_params):
      self.data.admin1 = sp.cast(init_params.admin1, sp.address)
      self.data.admin2 = sp.cast(init_params.admin2, sp.address)
      self.data.svls = sp.big_map({})
      self.data.mintPrice = sp.tez(10)
      self.data.requestFee = sp.tez(1)
      self.data.split = sp.nat(50)
      self.data.minTransferPrice = sp.tez(10)

    @sp.entrypoint
    def changeAdmin1(self, newAdmin):
      sp.cast(newAdmin, sp.address)
      assert sp.sender == self.data.admin1, "0"
      self.data.admin1 = newAdmin

    @sp.entrypoint
    def changeAdmin2(self, newAdmin):
      sp.cast(newAdmin, sp.address)
      assert sp.sender == self.data.admin2, "0"
      self.data.admin2 = newAdmin

    @sp.entrypoint
    def changeMintPrice(self, newMintPrice):
      sp.cast(newMintPrice, sp.mutez)
      assert sp.sender == self.data.admin1 or sp.sender == self.data.admin2, "0"
      self.data.mintPrice = newMintPrice

    @sp.entrypoint
    def changeSplit(self, newSplit):
      assert sp.sender == self.data.admin1 or sp.sender == self.data.admin2, "0"
      self.data.split = newSplit

    @sp.entrypoint
    def changeMinTransferPrice(self, newMinTransferPrice):
      sp.cast(newMinTransferPrice, sp.mutez)
      assert sp.sender == self.data.admin1 or sp.sender == self.data.admin2, "0"
      self.data.minTransferPrice = newMinTransferPrice

    @sp.entrypoint
    def changeRequestFee(self, newRequestFee):
      sp.cast(newRequestFee, sp.mutez)
      assert sp.sender == self.data.admin1 or sp.sender == self.data.admin2, "0"
      self.data.requestFee = newRequestFee

    @sp.entrypoint
    def requestTransfer(self, svl_key):
      sp.cast(svl_key, sp.string)
      svl = self.data.svls[svl_key]
      assert sp.amount == self.data.requestFee, "1"
      assert sp.sender != svl.owner, "5"
      assert svl.request == svl.owner, "6" 
      if self.data.requestFee != sp.mutez(0): 
        share = sp.split_tokens(sp.amount, 50, 100)
        sp.send(self.data.admin1, share)
        sp.send(self.data.admin2, share)
      svl.request = sp.sender
      self.data.svls[svl_key] = svl

    @sp.entrypoint
    def ownerClearTransferRequest(self, svl_key):
      sp.cast(svl_key, sp.string)
      svl = self.data.svls[svl_key]
      assert svl.owner == sp.sender, "3"
      svl.request = svl.owner
      svl.acceptRequest = False
      self.data.svls[svl_key] = svl

    @sp.entrypoint
    def ownerAcceptTransferRequest(self, svl_key):
      sp.cast(svl_key, sp.string)
      svl = self.data.svls[svl_key]
      assert svl.owner == sp.sender, "3"
      assert svl.request != svl.owner, "7"
      svl.acceptRequest = True
      self.data.svls[svl_key] = svl

    @sp.entrypoint 
    def requesterClearTransferRequest(self, svl_key):
      sp.cast(svl_key, sp.string)
      svl = self.data.svls[svl_key]
      assert svl.request == sp.sender, "4"
      svl.request = svl.owner
      svl.acceptRequest = False
      self.data.svls[svl_key] = svl

    @sp.entrypoint
    def changeTransferPrice(self, params):
      sp.cast(params.price, sp.mutez)
      sp.cast(params.svl_key, sp.string)
      svl = self.data.svls[params.svl_key]
      assert sp.sender == svl.owner, "3"
      assert params.price >= self.data.minTransferPrice, "1"
      svl.price = params.price
      self.data.svls[params.svl_key] = svl

    @sp.entrypoint
    def transfer(self, svl_key):
      sp.cast(svl_key, sp.string)
      svl = self.data.svls[svl_key]
      assert sp.amount == svl.price, "1"
      assert svl.owner != sp.sender, "8"
      assert svl.request == sp.sender, "4"
      assert svl.acceptRequest == True, "9"
      seller_share = sp.split_tokens(sp.amount, self.data.split, 100)
      if self.data.split != sp.nat(0): sp.send(sp.sender, seller_share)
      if self.data.split != sp.nat(100): 
          my_fee = sp.amount - seller_share
          my_fee_share = sp.split_tokens(my_fee, 50, 100)
          sp.send(self.data.admin1, my_fee_share)
          sp.send(self.data.admin2, my_fee_share)
      if svl.first_owner:
        svl.prev_owners_info = [(sp.now, svl.owner, svl.curr_owner_info)]
        svl.first_owner = False
      else:
        svl.prev_owners_info = sp.cons((sp.now, svl.owner, svl.curr_owner_info), svl.prev_owners_info)
      svl.curr_owner_info = ['']
      svl.acceptRequest = False
      svl.owner = svl.request
      self.data.svls[svl_key] = svl

    @sp.entrypoint
    def update(self, params): 
      sp.cast(params.svl_key, sp.string)
      sp.cast(params.curr_owner_info, sp.list[sp.string])
      svl = self.data.svls[params.svl_key]
      assert svl.owner == sp.sender, "3"
      assert len(params.curr_owner_info) < 100, "2"
      if not svl.first_owner:
        totalCids = len(params.curr_owner_info)
        for tuple in svl.prev_owners_info:
          (a, b, c) = tuple
          totalCids += len(c)
          assert totalCids < 100, "2"
      svl.curr_owner_info = params.curr_owner_info
      self.data.svls[params.svl_key] = svl
    
    @sp.entrypoint
    def mint(self, params):
      sp.cast(params.curr_owner_info, sp.list[sp.string])
      sp.cast(params.svl_key, sp.string)
      value_option = self.data.svls.get_opt(params.svl_key)
      assert value_option.is_none(), "10"
      assert sp.amount == self.data.mintPrice, "1"
      assert len(params.curr_owner_info) < 100, "2"
      if self.data.mintPrice != sp.mutez(0): 
        share = sp.split_tokens(sp.amount, 50, 100)
        sp.send(self.data.admin1, share)
        sp.send(self.data.admin2, share)
      self.data.svls[params.svl_key] = sp.record(
                                                price = self.data.minTransferPrice,
                                                prev_owners_info = [(sp.now, sp.sender, [''])],
                                                curr_owner_info = params.curr_owner_info,
                                                request = sp.sender,
                                                acceptRequest = False,
                                                first_owner = True,
                                                owner = sp.sender
                                              )

@sp.add_test()
def changeAdmins():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  new_admin1 = sp.test_account("new_admin1").address
  new_admin2 = sp.test_account("new_admin2").address
  pepe = sp.test_account("pepe").address
  
  scenario = sp.test_scenario("TestChangeAdmins", main)
  scenario.h1("Test change admins")
  scenario.p("Houfwgr")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract
  
  contract.changeAdmin1(pepe, _sender = pepe, _valid = False)

  contract.changeAdmin1(pepe, _sender = admin2, _valid = False)

  contract.changeAdmin1(new_admin1, _sender = pepe, _valid = False)

  contract.changeAdmin1(new_admin1, _sender = admin1)

  contract.changeAdmin1(new_admin2, _sender = new_admin1)

@sp.add_test()
def changeMintPrice():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address
  
  scenario = sp.test_scenario("TestChangeMintPrice", main)
  scenario.h1("Test change mint price")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  contract.changeMintPrice(sp.tez(2), _sender = pepe, _valid = False)

  contract.changeMintPrice(sp.tez(10), _sender = admin1)

  contract.changeMintPrice(sp.tez(20), _sender = admin2)

@sp.add_test()
def changeMinTransferPrice():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address
  
  scenario = sp.test_scenario("TestChangeMinTransferPrice", main)
  scenario.h1("Test change minimun transfer price")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  contract.changeMinTransferPrice(sp.tez(2), _sender = pepe, _valid = False)

  contract.changeMinTransferPrice(sp.tez(20), _sender = admin1)

@sp.add_test()
def changeRequestFee():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address
  
  scenario = sp.test_scenario("TestChangeRequestFee", main)
  scenario.h1("Test change request fee")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  contract.changeRequestFee(sp.tez(2), _sender = pepe, _valid = False)

  contract.changeRequestFee(sp.tez(2), _sender = admin1)

@sp.add_test()
def changeSplit():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address
  
  scenario = sp.test_scenario("TestChangeSplit", main)
  scenario.h1("Test change split")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  contract.changeSplit(sp.nat(10), _sender = pepe, _valid = False)

  contract.changeSplit(sp.nat(10), _sender = admin1)

@sp.add_test()
def mint():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address  
    
  scenario = sp.test_scenario("TestMint", main)
  scenario.h1("Test mint")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'b']
  )
  contract.mint(params, _sender = pepe, _amount = sp.tez(10))

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'b']
  )
  contract.mint(params, _sender = pepe, _amount = sp.tez(10), _valid = False)

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MfdsfATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'b']
  )
  contract.mint(params, _sender = pepe, _amount = sp.tez(8), _valid = False)

  params = sp.record(
    svl_key = '2021-12-31T23:59:645656',
    curr_owner_info = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',  '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',  '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58',  '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77',  '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96',  '97', '98', '99']
  )
  contract.mint(params, _sender = pepe, _amount = sp.tez(10), _valid = False)
 
  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfrewrewrLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',  '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',  '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58',  '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77',  '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96',  '97', '98', '99']
  )
  contract.mint(params, _sender = pepe, _amount = sp.tez(10))

@sp.add_test()
def changeTransferPrice():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address  
  pepa = sp.test_account("pepa").address
    
  scenario = sp.test_scenario("TestChangeTransferPrice", main)
  scenario.h1("Test change transfer price")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'b']
  )
  contract.mint(params, _sender = pepe, _amount = sp.tez(10))  

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    price = sp.tez(5)
  )
  contract.changeTransferPrice(params, _sender = pepa, _valid = False)  

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    price = sp.tez(5)
  )
  contract.changeTransferPrice(params, _sender = pepe, _valid = False)  

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    price = sp.tez(15)
  )
  contract.changeTransferPrice(params, _sender = pepe)  

@sp.add_test()
def update():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address
  pepa = sp.test_account("pepa").address 
    
  scenario = sp.test_scenario("TestUpdate", main)
  scenario.h1("Test update")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'b']
  )
  contract.mint(params, _sender = pepe, _amount = sp.tez(10))

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'c']
  )
  contract.update(params, _sender = pepe)

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'c']
  )
  contract.update(params, _sender = pepa, _valid = False)

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',  '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',  '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58',  '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77',  '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96',  '97', '98', '99']
  )
  contract.update(params, _sender = pepe, _valid = False)

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',  '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',  '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58',  '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77',  '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96',  '97', '98', '99']
  )
  contract.update(params, _sender = pepe)

  params = sp.record(
    svl_key = 'no key',
    curr_owner_info = ['a', 'c']
  )
  contract.update(params, _sender = pepe, _valid = False)

@sp.add_test()
def requestClearTransfer():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address
  pepa = sp.test_account("pepa").address
  pepi = sp.test_account("pepi").address
    
  scenario = sp.test_scenario("TestRequestClearTransfer", main)
  scenario.h1("Test request/clear transfer")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  params = sp.record(
    svl_key ='2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'b']
  )
  contract.mint(params, _sender = pepe, _amount = sp.tez(10))

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _amount = sp.tez(2), _valid = False)

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _amount = sp.tez(1))

  contract.requesterClearTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa)

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepe, _amount = sp.tez(1), _valid = False)

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _amount = sp.tez(1))

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepi, _amount = sp.tez(1), _valid = False)

  contract.requesterClearTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepi, _valid = False)

  contract.ownerClearTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepi, _valid = False)

  contract.ownerClearTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepe)

  contract.ownerAcceptTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _valid = False)

  contract.ownerAcceptTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepe, _valid = False)

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _amount = sp.tez(1))

  contract.ownerAcceptTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepe)

@sp.add_test()
def transferSVL():

  admin1 = sp.test_account("admin1").address
  admin2 = sp.test_account("admin2").address
  pepe = sp.test_account("pepe").address
  pepa = sp.test_account("pepa").address
  pepi = sp.test_account("pepi").address
  pepo = sp.test_account("pepo").address

  scenario = sp.test_scenario("TestTransfer", main)
  scenario.h1("Test transfer")
  init_params = sp.record(
    admin1 = admin1,
    admin2 = admin2,
  )
  contract = main.SmartContract(init_params)
  scenario += contract

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'b']
  )
  contract.mint(params, _sender=pepe, _amount = sp.tez(10))

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepe, _valid = False, _amount = sp.tez(10))

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _valid = False, _amount = sp.tez(10))

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _amount = sp.tez(1))

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _valid = False, _amount = sp.tez(10))

  contract.ownerAcceptTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepe)

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepi, _valid = False, _amount = sp.tez(10))

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _valid = False, _amount = sp.tez(9))

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _valid = False, _amount = sp.tez(11))

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa, _amount = sp.tez(10))

  params = sp.record(
    svl_key ='2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'd']
  )
  contract.update(params, _sender = pepe, _valid = False)

  params = sp.record(
    svl_key ='2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['mono']
  )
  contract.update(params, _sender = pepa)

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepi, _amount = sp.tez(1))

  contract.ownerAcceptTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepe, _valid = False)

  contract.ownerAcceptTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepa)

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepe, _amount = sp.tez(10), _valid = False, )

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepi, _amount = sp.tez(10))

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['a', 'd']
  )
  contract.update(params, _sender = pepa, _valid = False)

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['l', 'cafetera']
  )
  contract.update(params, _sender = pepi)

  params = sp.record(
    svl_key = '2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX',
    curr_owner_info = ['3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',  '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',  '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58',  '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77',  '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96',  '97', '98', '99']
  )
  contract.update(params, _sender = pepi, _valid = False)

  contract.requestTransfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepo, _amount = sp.tez(1))

  contract.ownerAcceptTransferRequest('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepi)

  contract.transfer('2021-12-31T23:59:59Ztz1iRXmfLXK5wWVok4MATJiw3UsgKkH9vrwX', _sender = pepo, _amount = sp.tez(10))