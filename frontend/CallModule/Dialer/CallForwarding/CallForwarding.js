import React from "react";
import { Button, View, Image, Text } from "react-native";
import { updatePreferences, getPreferences } from "../assets/library/api";
import { searchPeople } from "../CallListContainer/assets/library/api";
import loadingGif from "../../CallButton/assets/images/loading-gif.gif";
import deleteicon from "../CallListContainer/assets/images/deleteicon.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class CallForwarding extends React.Component {
  constructor(props) {
    super(props);
    this.initialForwardingObj = {
      number: "",
      duration: "10",
      name: ""
    };
    this.state = {
      alreadyAvailableNumbers: [],
      forwardedDetails: [],
      forwardingObj: { ...this.initialForwardingObj },
      isApiFetching: true,
      shouldDisplayTable: true,
      contactList: [],
      numberValidated: {
        status: false,
        errorMessage: "Not a valid name or number"
      }
    };
  }

  componentDidMount() {
    const { user } = this.props;
    this.getPreferenceInformation();
    const searchContactResponse = searchPeople(
      user.tenant_id,
      user.subtenant_id,
      user.identity,
      ""
    );
    searchContactResponse.then(async (response) => {
      const prepareOptionsForTypeAheadResponse =
        await this.prepareOptionsForTypeAhead(response.data);
      this.setState({
        ...this.state,
        contactList: [...prepareOptionsForTypeAheadResponse]
      });
    });
  }

  prepareOptionsForTypeAhead = (contactList) => {
    return new Promise((resolve) => {
      const { alreadyAvailableNumbers } = this.state;
      const tempContactList = [];
      let currentTreeNode = 0;
      contactList.map((element) => {
        element.numbers.map((ele) => {
          if (ele.number && !alreadyAvailableNumbers.includes(ele.number)) {
            const contactObj = { name: "", number: "", type: "" };
            contactObj.name = element.name === null ? ele.number : element.name;
            contactObj.label =
              element.name === null
                ? ele.number
                : `${element.name} (${ele.number})`;
            contactObj.number = ele.number;
            contactObj.type = ele.type;
            tempContactList.push(contactObj);
          }
        });
        currentTreeNode += 1;
        if (currentTreeNode === contactList.length) {
          resolve(tempContactList);
        }
      });
    });
  };

  setForwardingObj = (e) => {
    const { forwardingObj } = this.state;
    if (e.target.name === "duration") {
      forwardingObj.duration = e.target.value;
    }
    this.setState({
      ...this.state,
      forwardingObj: { ...this.state.forwardingObj }
    });
  };

  getPreferenceInformation = async () => {
    const { user } = this.props;
    const getPreferencesResponse = await getPreferences(
      user.tenant_id,
      user.subtenant_id,
      user.number
    );
    this.setState(
      {
        ...this.state,
        forwardedDetails: [...getPreferencesResponse.data.call_forwarding_rules]
      },
      () => {
        const tempAvaialbleNumbers = [];
        getPreferencesResponse.data.call_forwarding_rules.map((element) => {
          tempAvaialbleNumbers.push(element.number);
        });
        this.setState({
          ...this.state,
          alreadyAvailableNumbers: [...tempAvaialbleNumbers],
          isApiFetching: false
        });
      }
    );
  };

  setForwardedDetailsToState = () => {
    const { forwardingObj } = this.state;
    if (forwardingObj.number === "") {
      this.setState({
        ...this.state,
        numberValidated: { ...this.state.numberValidated, status: true }
      });
    } else {
      this.setState(
        {
          ...this.state,
          forwardedDetails: [...this.state.forwardedDetails, forwardingObj]
        },
        () => {
          this.setState({
            ...this.state,
            forwardingObj: { ...this.initialForwardingObj }
          });
        }
      );
    }
  };

  saveCallForwardingRules = () => {
    const { forwardedDetails } = this.state;
    const { user } = this.props;
    this.setState({ ...this.state, isApiFetching: true }, async () => {
      const updatePreferencesResponse = await updatePreferences(
        user.tenant_id,
        user.subtenant_id,
        user.number,
        forwardedDetails
      );

      if (updatePreferencesResponse.data === "success") {
        this.getPreferenceInformation();
        this.setState({ ...this.state, shouldDisplayTable: true });
      }
    });
  };

  alterDisplay = () => {
    this.setState({ ...this.state, shouldDisplayTable: false });
  };

  setSelected = (element) => {
    const { forwardingObj } = this.state;
    if (element.length === 0) {
      forwardingObj.number = "";
      forwardingObj.name = "";
    } else {
      const { forwardingObj } = this.state;
      forwardingObj.number = element[0].number;
      forwardingObj.name = element[0].name;
    }

    this.setState({
      ...this.state,
      forwardingObj: { ...this.state.forwardingObj }
    });
  };
  removeCallForwardingRules = (indexToBeRemoved) => {
    const { forwardedDetails } = this.state;
    const tempForwardedDetails = [...forwardedDetails];
    tempForwardedDetails.splice(indexToBeRemoved, 1);
    this.setState({
      ...this.state,
      forwardedDetails: [...tempForwardedDetails]
    });
  };

  render() {
    const {
      forwardingObj,
      forwardedDetails,
      isApiFetching,
      shouldDisplayTable,
      contactList,
      numberValidated
    } = this.state;
    const { handleDialer } = this.props;
    return (
      <View className="secondaryParticipant">
        <View className="mainboxheader">
          <View className="popupboxclose" onClick={() => handleDialer()}>
            <span>&#x00d7;</span>
          </View>
          <View className="contactuslist">
            <h4>Preferences</h4>
          </View>
        </View>
        <View className="preferencessec">
          {isApiFetching && (
            <View className="loadingicon">
              <Image
                alt="Loading"
                source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${loadingGif}`}
              />
            </View>
          )}
          <View className="callforwardcont">
            {!isApiFetching && (
              <View className="callforwardsec">
                <h4> Call Forwarding</h4>
                <View className="tablesec">
                  {forwardedDetails.map((element, index) => {
                    return (
                      <View className="phonebookbox" key={index}>
                        <View className="firsttext">
                          <View className="Nameletters">{index + 1}</View>
                        </View>
                        <View className="phonebooknum">
                          <View className="mainname">{element.name}</View>
                          <View className="mainnumber">{element.number}</View>
                          <View className="mainnumber">
                            Ring for {element.duration} Seconds
                          </View>
                        </View>
                        <View className="phonebookicon">
                          {
                            <button
                              className="removecolorbut forwardbut"
                              onClick={() =>
                                this.removeCallForwardingRules(index)
                              }
                              disabled={isApiFetching || !shouldDisplayTable}
                            >
                              <Image
                                source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${deleteicon}`}
                              />
                            </button>
                          }
                        </View>
                      </View>
                    );
                  })}
                </View>
                {shouldDisplayTable && (
                  <button
                    className="forwardbut"
                    onClick={() => this.alterDisplay()}
                    disabled={isApiFetching}
                    title="Add New"
                  >
                  </button>
                )}
              </View>
            )}

            {!isApiFetching && !shouldDisplayTable && (
              <View className="callforwardsec">
                <View className="selectboxsec">
                  <h3>To:</h3>
                  <Text
                    id="basic-example"
                    onChange={(e) => this.setSelected(e)}
                    options={contactList}
                    placeholder="Self or Number or Name"
                    filterBy={["number"]}
                  ></Text>
                  {numberValidated.status && (
                    <View>
                      <span>{numberValidated.errorMessage}</span>
                    </View>
                  )}

                  {isApiFetching && (
                    <View>
                      <Image
                        alt="Loading"
                        source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${loadingGif}`}
                        srcset="Loading"
                      />
                    </View>
                  )}

                  <View className="selectboxsec">
                    <h3>Ring For:</h3>
                    <View className="selecrbox">
                      <select
                        id="duration"
                        name="duration"
                        onChange={(e) => this.setForwardingObj(e)}
                        value={forwardingObj.duration}
                      >
                        <option value="15">3 Rings (15 Seconds)</option>
                        <option value="30">6 Rings (30 Seconds)</option>
                        <option value="45">9 Rings (45 Seconds)</option>
                        <option value="60">12 Rings (60 Seconds)</option>
                        <option value="90">15 Rings (90 Seconds)</option>
                        <option value="120">24 Rings (120 Seconds)</option>
                      </select>
                    </View>
                  </View>
                </View>

                <button
                  className="forwardbut"
                  onClick={() => this.setForwardedDetailsToState()}
                  disabled={isApiFetching}
                >
                  Done
                </button>
                <button
                  className="forwardbut"
                  onClick={() =>
                    this.setState({ ...this.state, shouldDisplayTable: true })
                  }
                  disabled={isApiFetching}
                  title="Cancel"
                >
                </button>
              </View>
            )}
          </View>
          <View className="bottomfixbut">
            <button
              className="allsave forwardbut"
              onClick={() => this.saveCallForwardingRules()}
            >
              Save Preferences
            </button>
          </View>
        </View>
      </View>
    );
  }
}

export default CallForwarding;
