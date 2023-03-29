import React from "react";
import { Button, View, Image, Text,TextInput } from "react-native";
import { searchPeople } from "../assets/library/api";
import searchicon from "../assets/images/searchicon.svg";
import smallcallicon from "../assets/images/smallcallicon.svg";
import calloptionicon from "../assets/images/calloptionicon.svg";
import smallmessageicon from "../assets/images/smallmessageicon.svg";
import loadingGif from "../../../CallButton/assets/images/loading-gif.gif";
import { displayContactInitial } from "../assets/library/helper";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;
import Icon from "react-native-vector-icons/FontAwesome5";

class ContactList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isApiFetching: false,
      contactList: [],
      timer: null,
      target: null,
      shouldDisplayPopup: false,
      currentContactElement: [],
      contactListActionType: null,
      processingAddOrTransferParticipant: false
    };
  }

  searchContact = (e) => {
    const { value } = e.target; // TODO: change later for actual implementation once NCAMEO team alter the API
    if (value !== "") {
      const { user } = this.props;
      const { timerWillStart } = this.state;
      clearTimeout(timerWillStart);
      const timer = setTimeout(() => {
        this.setState({ ...this.state, isApiFetching: true });
        const searchContactResponse = searchPeople(
          user.tenant_id,
          user.subtenant_id,
          user.identity,
          value
        );
        searchContactResponse.then((contact) => {
          this.setState({
            ...this.state,
            contactList: contact.data,
            isApiFetching: false
          });
        });
      }, 2000);
      this.setState({ ...this.state, timerWillStart: timer });
    }
  };

  prepareItemAction = async (e, contactElement, actionType) => {
    this.setState({ ...this.state, processingAddOrTransferParticipant: true });
    const { makeOutBoundCall } = this.props;
    if (contactElement.numbers.length <= 1) {
      if (actionType === "call" || actionType === "") {
        makeOutBoundCall(contactElement.numbers[0].number, contactElement.name);
      } else if (actionType === "addParticipant") {
        window.addConferenceParticipantInit(
          contactElement.numbers[0].number,
          contactElement.name
        );
      } else if (actionType === "transfer") {
        window.processCallTransfer(
          contactElement.numbers[0].number,
          contactElement.name
        );
      } else {
        window.startCreateatingConversation(
          contactElement.numbers[0].number,
          contactElement,
          true
        );
      }
    } else {
      this.setState(
        {
          ...this.state,
          target: e.target,
          currentContactElement: contactElement,
          contactListActionType: actionType
        },
        () =>
          this.setState({
            ...this.state,
            shouldDisplayPopup: !this.state.shouldDisplayPopup
          })
      );
    }
  };

  popover = () => {
    const { makeOutBoundCall, activeCallCount } = this.props;
    const { currentContactElement, contactListActionType } = this.state;
    return (
      <Popover id="popover-basic">
        <Popover.Body>
          <ul>
            {currentContactElement.numbers.map((element, index) => (
              <li
                key={index}
                onClick={() =>
                  `${
                    contactListActionType === "call" ||
                    contactListActionType === "" ||
                    contactListActionType === "addParticipant"
                      ? activeCallCount === 0
                        ? makeOutBoundCall(
                            element.number,
                            currentContactElement.name
                          )
                        : window.addConferenceParticipantInit(
                            element.number,
                            currentContactElement.name
                          )
                      : contactListActionType === "transfer"
                      ? window.processCallTransfer(
                          element.number,
                          currentContactElement.name
                        )
                      : window.startCreateatingConversation(
                          element.number,
                          element,
                          true
                        )
                  }`
                }
              >
                <Image
                  alt=""
                  className="calldropicon"
                  source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${calloptionicon}`}
                />{" "}
                {element.number}
              </li>
            ))}
          </ul>
        </Popover.Body>
      </Popover>
    );
  };

  isSelfContact = (contactElement) => {
    const { user } = this.props;
    const selfContact = contactElement.numbers.filter(
      (element) => element.number === user.number
    );
    return selfContact.length > 0 ? true : false;
  };

  isContactAlreadyOnACall = (contactElement) => {
    const { numbersInCalls } = this.props;
    const isOnCall = contactElement.numbers.filter((element) =>
      numbersInCalls.includes(element.number)
    );
    return isOnCall.length > 0 ? true : false;
  };

  render() {
    const {
      contactList,
      isApiFetching,
      target,
      shouldDisplayPopup,
      currentContactElement,
      processingAddOrTransferParticipant
    } = this.state;
    const { handleDialer, actionType, activeCallCount } = this.props;
    return (
      <View className="secondaryParticipant">
        <View className="mainboxheader">
          <View className="popupboxclose" onClick={() => handleDialer()}>
            <Text>&#x00d7;</Text>
          </View>
          <View className="contactuslist">
            <Text>Contacts</Text>
          </View>
        </View>
        <View className="searchboxsec">
          <TextInput
            type="text"
            name="contactSearchInput"
            id="contactSearchInput"
            placeholder="Search Contacts"
            onChange={(e) => this.searchContact(e)}
            onKeyDown={() => {
              const { timerWillStart } = this.state;
              clearTimeout(timerWillStart);
            }}
          />
          <Icon name={"search"} ></Icon>
        </View>
        <View className="phonebooklist phonebooklist">
          {isApiFetching && (
            <Image
              alt=""
              className="logingicon"
              source={'https://painterbros-stage.regalixtools.com/CallButton/assets/images/loading-gif.gif'}
            />
          )}
          {!isApiFetching &&
            contactList.length > 0 &&
            contactList.map((contactElement, index) => {
              return (
                <View className="phonebookbox" key={index}>
                  <View className="firsttext">
                    <View className="Nameletters">
                      <Text>
                        {displayContactInitial(
                          contactElement.name === null
                            ? contactElement.numbers[0].number
                            : contactElement.name
                        )}
                      </Text>
                    </View>
                  </View>
                  <View className="phonebooknum">
                    <Text
                      data-bs-toggle="tooltip"
                      data-bs-placement="bottom"
                      title={
                        contactElement.name === null
                          ? contactElement.numbers[0].number
                          : contactElement.name
                      }
                    >
                      {contactElement.name === null
                        ? contactElement.numbers[0].number
                        : contactElement.name}
                    </Text>
                    <Text className={`phonebook${contactElement.type}`}>
                      {contactElement.type}
                    </Text>
                    <Text>{contactElement.numbers[0].number}</Text>
                  </View>

                  <View className="phonebookicon">
                    <Button
                      id={contactElement.numbers[0].number}
                      className="removecolorbut smallcallicon"
                      onClick={(e) =>
                        this.prepareItemAction(e, contactElement, "sms")
                      }
                      disabled={
                        actionType === "call" ||
                        actionType === "transfer" ||
                        processingAddOrTransferParticipant ||
                        this.isSelfContact(contactElement)
                      }
                    >
                      <Image
                        alt=""
                        source={'https://painterbros-stage.regalixtools.com/static/media/smallmessageicon.b9f11a0ad71342fd8168b44722542a5a.svg'}
                      />
                      {/* <Icon name={"envelope"} ></Icon> */}
                    </Button>

                    <Button
                      id={contactElement.numbers[0].number}
                      className="removecolorbut smallcallicon"
                      onClick={(e) =>
                        this.prepareItemAction(e, contactElement, actionType)
                      }
                      disabled={
                        actionType === "conversation" ||
                        (actionType === "" && activeCallCount > 0) ||
                        processingAddOrTransferParticipant ||
                        this.isSelfContact(contactElement) ||
                        (actionType === "transfer" &&
                          contactElement.type.toLowerCase() !== "user") ||
                        this.isContactAlreadyOnACall(contactElement)
                      }
                    >
                      <Image
                        alt=""
                        source={'https://painterbros-stage.regalixtools.com/static/media/smallcallicon.89f8f23e3a7c9aa58c9443af0485b462.svg'}
                      />
                      {/* <Icon name={"phone"} ></Icon> */}
                    </Button>
                  </View>
                </View>
              );
            })}
          {shouldDisplayPopup && (
            <Overlay
              show={shouldDisplayPopup}
              target={target}
              placement="bottom"
              containerPadding={20}
            >
              {this.popover(currentContactElement)}
            </Overlay>
          )}

          {!isApiFetching && contactList.length === 0 && (
            <View className="noresult "><Text>No results found</Text></View>
          )}
        </View>
      </View>
    );
  }
}

export default ContactList;
