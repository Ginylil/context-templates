'use strict';
// Synthetic stress model. Linked diagrams preserve one shared Order identity.
const DemoModel = (() => {
  const groups = [
    {id:'purchase', label:'Purchase & items', direct:[
      'Customer','Cart','LineItem','Product','Price','Discount','Tax','Invoice','Subscription'],
      extra:['CustomerProfile','CartItem','ProductVariant','Category','Catalog','Review','Coupon','Money']},
    {id:'fulfilment', label:'Fulfilment & stock', direct:[
      'Shipment','Delivery','Address','Warehouse','Inventory','Reservation','Package','Carrier','TrackingEvent'],
      extra:['StockMovement','Supplier','PurchaseOrder','Location','StockCount','ReturnShipment']},
    {id:'settlement', label:'Payment & settlement', direct:[
      'Payment','CardPayment','WalletPayment','Refund','Receipt','PaymentAttempt','FraudReview','Chargeback','Settlement'],
      extra:['PaymentMethod','Transaction','LedgerEntry','Account','Payout','Dispute']}
  ];
  const id = label => label.replace(/[A-Z]/g,(c,i)=>(i?'-':'')+c.toLowerCase());
  const nodes = [{id:'order',label:'Order',domain:'shared',
    fields:['− id: UUID','− status: Status'],methods:['+ total()'],
    detail:'A shared order identity appears in three linked diagrams. Its 27 direct relationships are divided by subject; this is a reading aid, not an endorsement of a highly coupled domain model.'}];
  const edges = [], views = [];
  const descriptions = {
    customer:'places',cart:'starts from','line-item':'contains',product:'references',
    price:'uses',discount:'applies',tax:'calculates',invoice:'documents',subscription:'renews',
    shipment:'dispatches',delivery:'delivers to',address:'ships to',warehouse:'fulfilled by',
    inventory:'checks',reservation:'reserves',package:'packs',carrier:'carried by','tracking-event':'tracks',
    payment:'paid by','card-payment':'uses card','wallet-payment':'uses wallet',refund:'refunded by',
    receipt:'receipted by','payment-attempt':'attempts','fraud-review':'reviewed by',chargeback:'disputed by',settlement:'settled by'
  };
  function relation(from,to,label,view,kind='association') {
    const edge = {id:`${from}-${to}`,from,to,label,view,kind,
      detail:kind==='composition'?'Composition: the filled diamond belongs at Order, the whole.':
        kind==='inheritance'?'Generalization: the hollow triangle points to Payment, the parent.':
          `${from} ${label} ${to}. Association in a synthetic teaching model; cardinality is deliberately unspecified.`};
    if (kind==='composition') Object.assign(edge,{sourceMultiplicity:'1',targetMultiplicity:'1..*'});
    edges.push(edge); return edge.id;
  }
  for (const group of groups) {
    const members = ['order'];
    for (const label of [...group.direct,...group.extra]) {
      const key=id(label); members.push(key);
      nodes.push({id:key,label,domain:group.id,fields:['− id: UUID'],methods:['+ inspect()'],
        detail:`${label} in the ${group.label.toLowerCase()} diagram. Its minimal members are illustrative, not extracted from production code.`});
    }
    const edgeIds = group.direct.map(label=>{
      const key=id(label),kind=key==='line-item'?'composition':'association';
      return relation('order',key,descriptions[key],group.id,kind);
    });
    group.extra.forEach((label,i)=>edgeIds.push(relation(id(group.direct[i%group.direct.length]),id(label),
      'relates to',group.id)));
    if (group.id==='settlement') {
      edgeIds.push(relation('card-payment','payment','specializes',group.id,'inheritance'));
      edgeIds.push(relation('wallet-payment','payment','specializes',group.id,'inheritance'));
    }
    views.push({id:group.id,label:group.label,nodes:members,edges:edgeIds});
  }
  nodes.forEach((node,i)=>node.home={x:(i%8)*280,y:Math.floor(i/8)*190});
  const tour = [
    {view:'purchase',focus:'order',title:'Order anchors the purchase.',
      body:'Its nine direct neighbors move closer. Every relationship in this neighborhood remains visible.'},
    {view:'purchase',focus:'product',title:'Travel to Product.',
      body:'The camera follows the class. Product’s direct neighbors gather around it; unrelated classes recede.'},
    {view:'purchase',focus:'customer',title:'A smaller neighborhood, at reading size.',
      body:'The focus window adapts to the local relationships instead of shrinking the whole model to fit.'},
    {view:'fulfilment',focus:'order',title:'The same Order, another diagram.',
      body:'Order has 27 direct relationships overall. They are split into three linked diagrams, each below the limit of 20.'},
    {view:'fulfilment',focus:'warehouse',title:'Follow Warehouse into stock.',
      body:'Distance in the original map does not prevent a direct neighbor from joining the focused neighborhood.'},
    {view:'fulfilment',focus:'shipment',title:'Follow a relationship to Shipment.',
      body:'Zoom out or drag at any moment. That pauses the tour and leaves the camera under your control.'},
    {view:'settlement',focus:'order',title:'Order enters the settlement view.',
      body:'The shared class keeps its identity. A linked view changes the reading scope, never the underlying relationships.'},
    {view:'settlement',focus:'payment',title:'Payment has specializations.',
      body:'Hollow triangles still point to Payment. Repositioning preserves UML direction, ownership and relationship meaning.'}
  ];
  return {nodes,edges,views,tour,maxRelations:20};
})();
if (typeof module!=='undefined') module.exports=DemoModel;
