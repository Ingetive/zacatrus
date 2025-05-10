API_OPERATIONS_MAPPING = {
    'createFeed': {
        'url_path': '/feeds/2021-06-30/feeds',
        'restricted_resource_path': None,
    },
    'createFeedDocument': {
        'url_path': '/feeds/2021-06-30/documents',
        'restricted_resource_path': None,
    },
    'createRestrictedDataToken': {
        'url_path': '/tokens/2021-03-01/restrictedDataToken',
        'restricted_resource_path': None,
    },
    'getMarketplaceParticipations': {
        'url_path': '/sellers/v1/marketplaceParticipations',
        'restricted_resource_path': None,
    },
    'getOrders': {
        'url_path': '/orders/v0/orders',
        'restricted_resource_path': '/orders/v0/orders',
        'restricted_resource_data_elements': ['buyerInfo', 'shippingAddress'],
    },
    'getOrderItems': {
        'url_path': '/orders/v0/orders/{param}/orderItems',
        # Amazon requires the path to include the placeholder "{orderID}" to grant the RDT.
        'restricted_resource_path': '/orders/v0/orders/{orderId}/orderItems',
        'restricted_resource_data_elements': ['buyerInfo']
    },
    'getInboundShipments': {
        'url_path': '/fba/inbound/v0/shipments',
        'restricted_resource_path': '/fba/inbound/v0/shipments',
        'restricted_resource_data_elements': [],
    },
}