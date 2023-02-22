import React from "react";
import moment from "moment";
import { fancyTimeFormat } from "../assets/library/helper";
import { Button, Image, Text, View } from "react-native";
import ConferenceParticipantDetails from "./ConferenceParticipantDetails";
import {
  displayContactInitial,
  countTheCallsOnHold
} from "../assets/library/helper";
import infoicon from "../assets/images/infoicon.svg";
import avataricon from "../assets/images/avataricon.svg"
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class ParticipantDetails extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      showDisplayParticipantComponent: false,
      currentCallDuration: 0,
      logTimer: null
    };
  }

  componentDidMount() {
    const { alterButtonDiableProperty } = this.props;
    this.setCallDuration();
    alterButtonDiableProperty(false);
  }

  componentWillUnmount() {
    const { logTimer } = this.state;
    clearInterval(logTimer);
    this.setState({ ...this.state, logTimer: null });
  }

  startCallDuration = () => {
    const logTimer = setInterval(() => {
      let { currentCallDuration } = this.state;
      const duration = currentCallDuration + 1;
      this.setState({ ...this.state, currentCallDuration: duration });
    }, 1000);
    this.setState({ ...this.state, logTimer });
  };

  setCallDuration = () => {
    const { callElement } = this.props;
    const conferenceStartTime = moment
      .utc(callElement.conference.startTime)
      .local()
      .format("MMM DD YYYY h:mm:ss A");
    const date = new Date();
    const now_utc = Date.UTC(
      date.getUTCFullYear(),
      date.getUTCMonth(),
      date.getUTCDate(),
      date.getUTCHours(),
      date.getUTCMinutes(),
      date.getUTCSeconds()
    );
    const currentUtcTime = moment(new Date(now_utc));
    let duration =
      moment.duration(currentUtcTime.diff(conferenceStartTime))._milliseconds /
      1000;

    this.setState({ ...this.state, currentCallDuration: duration }, () =>
      this.startCallDuration()
    );
  };

  shouldComponentUpdate(nextProps) {
    const { showDisplayParticipantComponent } = this.state;
    if (
      showDisplayParticipantComponent &&
      nextProps.callElement.conference.participants.length === 2
    ) {
      this.setState({ ...this.state, showDisplayParticipantComponent: false });
    }
    return true;
  }

  checkParticipantStatus = (participants) => {
    const participantsStatusCount = participants.filter(
      (element) =>
        element.callStatus === "in-progress" ||
        element.callStatus === "completed"
    );
    if (participantsStatusCount.length === participants.length) {
      return true;
    }
    return false;
  };

  toogleParticipantComponent = () => {
    const { showDisplayParticipantComponent } = this.state;
    const { toggleDisplayPrimaryActionButton } = this.props;
    toggleDisplayPrimaryActionButton();
    this.setState({
      ...this.state,
      showDisplayParticipantComponent: !showDisplayParticipantComponent
    });
  };

  getNumberOfActiveParticipants = (participants) => {
    const activeParticipantArray = participants.filter(
      (participant) =>
        participant.type !== "destination" &&
        participant.type !== "source" &&
        participant.callStatus === "in-progress"
    );
    return Number(activeParticipantArray.length);
  };

  render() {
    const {
      participantElement,
      participants,
      conn,
      callElement,
      removeParticipant,
      toggleDisplayPrimaryActionButton,
      conferenceStatus,
      alterDisplayIndividualCallDetails,
      callDetails,
      user,
      alterButtonDiableProperty
    } = this.props;
    const { currentCallDuration, showDisplayParticipantComponent } = this.state;
    return (
      <View>
        {showDisplayParticipantComponent &&
          callElement.conference.participants.length > 2 && (
            <ConferenceParticipantDetails
              callElement={callElement}
              removeParticipant={removeParticipant}
              conn={conn}
              toogleParticipantComponent={this.toogleParticipantComponent}
              toggleDisplayPrimaryActionButton={
                toggleDisplayPrimaryActionButton
              }
              user={user}
              alterButtonDiableProperty={alterButtonDiableProperty}
            />
          )}
        {callDetails && !showDisplayParticipantComponent && (
          <View>
            {Object.values(callDetails).length >= 1 &&
              countTheCallsOnHold(callDetails) > 0 && (
                <View className="col-md-12 holdCallParentDiv">
                  <View className="col-md-10 holdCallDivText">
                    {`${countTheCallsOnHold(callDetails) === 1
                        ? "1 call is on hold"
                        : `${countTheCallsOnHold(
                          callDetails
                        )} calls are on hold`
                      }`}
                  </View>
                  <View className="col-md-2 holdCallDivlink">
                    <button
                      className="viewCallsOnHoldBtn"
                      onPress={() => alterDisplayIndividualCallDetails(false)}
                      value="View"
                    >

                    </button>
                  </View>
                </View>
              )}
            <View className="callnametext">
              <ul>
                <li>
                  <p>
                    {console.log(participantElement)}
                    {participantElement.name &&
                      participantElement.name === participantElement.to ? (
                      <Image
                        source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${avataricon}`}
                      />
                    ) : (
                      displayContactInitial(participantElement.name)
                    )}
                  </p>
                </li>
              </ul>
            </View>
            <View className="displayCallNameContainer">
              <View className="firsttext">
                <View className="Nameletters">
                  <span>{displayContactInitial(participantElement.name)}</span>
                </View>
              </View>
            </View>
            <View className="phonebooknum">
              <View
                className="maincallname"
                data-bs-toggle="tooltip"
                data-bs-placement="bottom"
                title={
                  participantElement.name === null
                    ? participantElement.direction === "inbound"
                      ? participantElement.from_
                      : participantElement.to
                    : participantElement.name
                }
              >
                {participantElement.name === null
                  ? participantElement.direction === "inbound"
                    ? participantElement.from_
                    : participantElement.to
                  : participantElement.name}
                {participants &&
                  participants.length > 2 &&
                  Number(this.getNumberOfActiveParticipants(participants)) >
                  0 && (
                    <View className="conferencecallnum">
                      +{this.getNumberOfActiveParticipants(participants)}
                      <Button
                        className="removecolorbut infoicon"
                        onPress={() => this.toogleParticipantComponent()}
                      >
                        <Image
                          source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${infoicon}`}
                        />
                      </Button>
                    </View>
                  )}
              </View>
              {participants && participants.length > 2 && (
                <Text>Conference Call</Text>
              )}
              <View className="maincallnumber">
                {participantElement.direction === "inbound"
                  ? participantElement.from_
                  : participantElement.to}
              </View>
              <Text className="maincallringing">{conferenceStatus}</Text>
              {["in-progress", "hold"].includes(conferenceStatus) && (
                <Text className="maincallringing">
                  {fancyTimeFormat(currentCallDuration)}
                </Text>
              )}
            </View>
          </View>
        )}
      </View>
    );
  }
}

export default ParticipantDetails;
