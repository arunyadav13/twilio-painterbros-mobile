import React from "react";
import PrimaryParticipant from "./PrimaryParticipant";
import SecondaryParticipant from "./SecondaryParticipant";

class CallContainer extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const {
      callElement,
      addNewParticipant,
      removeParticipant,
      conn,
      toggleDisplayPrimaryActionButton,
      callDetails,
      alterDisplayIndividualCallDetails,
      user,
      alterButtonDiableProperty,
      shouldDisableButton
    } = this.props;
    return (
      <div>
        {callElement.conference.participants.map(
          (participantElement, index) => {
            if (
              callElement.call.direction === "outbound-api" ||
              callElement.call.direction === "inbound"
            ) {
              if (
                (callElement.call.direction === "inbound" &&
                  participantElement.type === "source") ||
                (callElement.call.direction === "outbound-api" &&
                  participantElement.type === "destination")
              ) {
                return (
                  <PrimaryParticipant
                    callElement={callElement}
                    participantElement={participantElement}
                    addNewParticipant={addNewParticipant}
                    removeParticipant={removeParticipant}
                    key={`pp-${index}`}
                    conn={conn}
                    participants={callElement.conference.participants}
                    toggleDisplayPrimaryActionButton={
                      toggleDisplayPrimaryActionButton
                    }
                    conferenceStatus={callElement.conference.status}
                    callDetails={callDetails}
                    alterDisplayIndividualCallDetails={
                      alterDisplayIndividualCallDetails
                    }
                    user={user}
                    shouldDisableButton={shouldDisableButton}
                    alterButtonDiableProperty={alterButtonDiableProperty}
                  />
                );
              } else {
                return (
                  (participantElement.type === "warm-transfer" ||
                    participantElement.type === "") &&
                  participantElement.callStatus !== "in-progress" && (
                    <SecondaryParticipant
                      callElement={callElement}
                      participantElement={participantElement}
                      addNewParticipant={addNewParticipant}
                      removeParticipant={removeParticipant}
                      key={`sp-${index}`}
                      conn={conn}
                      user={user}
                      alterButtonDiableProperty={alterButtonDiableProperty}
                      shouldDisableButton={shouldDisableButton}
                    />
                  )
                );
              }
            }
          }
        )}
      </div>
    );
  }
}

export default CallContainer;
